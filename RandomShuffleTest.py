import random

from BasicTest import BasicTest

class RandomShuffleTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)
        
        random.shuffle(self.forwarder.out_queue)
        
        # empty out the in_queue
        self.forwarder.in_queue = []
