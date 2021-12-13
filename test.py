import socos.watchdog as w

watch = w.Watchdog()

while True:
    watch.toggle(500)