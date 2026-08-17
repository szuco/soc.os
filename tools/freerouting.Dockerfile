# Freerouting 1.9.0 in einem Linux-Container.
#
#   docker build -f tools/freerouting.Dockerfile -t switchstack-freerouting tools/
#
# WOZU DAS DA IST
# ---------------
# Die Routing-Pipeline (tools/route_boards.py) besteht aus drei Schritten:
# DSN exportieren, routen, SES zurueckimportieren. Der erste und der dritte
# laufen ueber die pcbnew-API und damit ueberall - auch auf macOS. Nur der
# mittlere braucht ein X-Display: Freerouting 1.9.0 ist keine echte
# Konsolenanwendung, es instanziiert AWT-Klassen, auch im Batchbetrieb.
#
# Unter Linux loest xvfb-run das. Auf macOS gibt es kein Xvfb - und genau
# deshalb dieser Container. Er enthaelt nichts als eine JRE, Xvfb und das
# Jar; gemountet wird das Arbeitsverzeichnis mit der DSN-Datei.
#
# WARUM 1.9.0 UND NICHT 2.x
# --------------------------
# Version 2.1.0 headless hat sich als unbrauchbar erwiesen: -mp wird
# ignoriert, Float-Optionen sind per CLI nicht setzbar, und die exportierte
# SES stammt von einem aelteren Zwischenstand statt vom Endergebnis - sechs
# Netze fehlten, obwohl das Log null unrouted meldete. 1.9.0 routet klassisch
# und exportiert vollstaendig.

# Die JRE-Version haengt an Freerouting: 1.9.0 laeuft auf 21, 2.3.0 verlangt
# Java 25 (Class-File-Version 69). Deshalb parametriert.
ARG JRE_TAG=21-jre
FROM eclipse-temurin:${JRE_TAG}

# xvfb ist das Einzige, was ueber die JRE hinaus gebraucht wird. libxrender
# und libxtst holt AWT nach, sonst bricht die Klasseninitialisierung ab.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      xvfb libxrender1 libxtst6 libxi6 fontconfig \
 && rm -rf /var/lib/apt/lists/*

ARG FREEROUTING_VERSION=1.9.0
ADD https://github.com/freerouting/freerouting/releases/download/v${FREEROUTING_VERSION}/freerouting-${FREEROUTING_VERSION}.jar /opt/freerouting.jar
RUN chmod 0444 /opt/freerouting.jar

WORKDIR /work

# XVFB-RUN DARF NICHT PID 1 SEIN
# ------------------------------
# xvfb-run startet Xvfb im Hintergrund und wartet dann auf ein SIGUSR1, mit
# dem Xvfb seine Bereitschaft meldet (Zeile 180 des Skripts: "trap : USR1",
# darunter "(trap '' USR1; exec Xvfb ...)"). Als PID 1 eines Containers kommt
# dieses Signal nicht an - der Kernel stellt an PID 1 nur Signale zu, fuer die
# ein Handler installiert ist, und die Zustellung durch das wait des Shell-
# Interpreters verhaelt sich dort anders. Ergebnis: Xvfb laeuft, xvfb-run
# steht, und java wird NIE gestartet. Der Container haengt bei 0 % CPU, bis
# irgendein Timeout zuschlaegt - genau das ist am 16.08.2026 zweimal passiert.
#
# Der Ausweg ist ein Wrapper OHNE exec: Dann ist das Wrapper-Skript PID 1 und
# xvfb-run ein gewoehnliches Kind mit normaler Signalzustellung.
RUN printf '%s\n' \
      '#!/bin/sh' \
      '# Kein exec - xvfb-run muss ein Kind bleiben, sonst haengt es als PID 1.' \
      'xvfb-run -a java -jar /opt/freerouting.jar "$@"' \
      > /usr/local/bin/freerouting \
 && chmod +x /usr/local/bin/freerouting

# Die Argumente kommen von route_boards.py: -de <dsn> -do <ses> -mp <passes>
# -dct 0 -oit 0.5.
ENTRYPOINT ["/usr/local/bin/freerouting"]
