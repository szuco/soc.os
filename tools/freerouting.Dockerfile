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

FROM eclipse-temurin:21-jre

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

# Die Argumente kommen von route_boards.py: -de <dsn> -do <ses> -mp <passes>
# -dct 0 -oit 0.5. Der Container ist damit ein reiner Ersatz fuer den
# lokalen Aufruf "xvfb-run -a java -jar freerouting.jar ...".
ENTRYPOINT ["xvfb-run", "-a", "java", "-jar", "/opt/freerouting.jar"]
