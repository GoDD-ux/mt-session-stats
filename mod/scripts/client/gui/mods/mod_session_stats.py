from gui.session_stats.controller import g_controller


def init():
    g_controller.start()


def fini():
    g_controller.stop()
