import random

from BasicTest import BasicTest


class SackRandomShuffleTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackRandomShuffleTest, self).__init__(forwarder, input_file, sackMode=True)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)

        random.shuffle(self.forwarder.out_queue)

        # empty out the in_queue
        self.forwarder.in_queue = []
