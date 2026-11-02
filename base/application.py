import signal
import sys
from django.core.management import execute_from_command_line


def application():
    @classmethod
    def initialiaze(cls):
        execute_from_command_line([sys.argv[0], "migrate"])

        from django.contrib.auth.models import User

        if User.objects.count() == 0:
            execute_from_command_line([sys.argv[0], "loaddata", "auth.json"])

        # from apps.scheduler.core.cluster import QCluster
        #
        # def sigint_handler(signal, frame):
        #     global q_cluster
        #     q_cluster.stop()
        #     sys.exit(0)
        #
        # global q_cluster
        # q_cluster = QCluster()
        # signal.signal(signal.SIGINT, sigint_handler)
