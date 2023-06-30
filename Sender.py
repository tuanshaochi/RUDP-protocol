import sys
import time
import getopt
import pickle
import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Msg:
    def __init__(self, msg, seqno, timestamp):
        self.msg = msg
        self.seqno = seqno
        self.timestamp = timestamp


class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug, sackMode,binaMode,window_size, send_timeout, receive_timeout):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.window_size = window_size
        self.send_timeout = send_timeout
        self.receive_timeout = receive_timeout
        self.sackMode = False
        self.binaMode=False
        if sackMode:
            self.sackMode = True
        if binaMode:
            self.binaMode = True

        if filename == None:
            self.infile = sys.stdin
        elif self.binaMode:
            self.infile = open(filename,"rb+")
        else:
            self.infile = open(filename,"r")

    def handle_response(self, response_packet):
        if Checksum.validate_checksum(response_packet):
            print("recv: %s" % response_packet)
            return True
        else:
            print("recv: %s <--- CHECKSUM FAILED" % response_packet)
            return False

    def make_packet_bina(self, msg_type, seqno, msg):
        msg_package = {'msg_type': msg_type, 'seqno': seqno, 'msg': msg}
        checksum = Checksum.generate_checksum_bina(pickle.dumps(msg_package))
        msg_package['checksum'] = checksum
        return pickle.dumps(msg_package)

    def split_packet_bina(self, message):
        msg_package = pickle.loads(message)
        msg_type = msg_package["msg_type"]
        seqno = msg_package["seqno"]
        msg = msg_package["msg"]
        checksum = msg_package["checksum"]
        return msg_type, seqno, msg, checksum
    
    def send_bina(self, message, address=None):
        if address is None:
            address = (self.dest,self.dport)
        self.sock.sendto(message, address)

    # Main sending loop.
    def start(self):
        msg = []
        pointer = 0
        next_seqno = 0
        next_msg = self.infile.read(500)
        
        while len(msg) != 0 or next_msg != "" and next_msg != b"":
            if next_msg != "" and next_msg != b"":  # 添加新消息
                if len(msg) == 0:
                    msg.append(Msg(next_msg, next_seqno, 0.0))
                    next_msg = self.infile.read(500)
                    next_seqno += 1
                elif next_seqno - msg[0].seqno < self.window_size and len(msg) < self.window_size:
                    # 如果下一次传消息在窗口内，且窗口未满，那么就将新消息封装入窗口
                    msg.append(Msg(next_msg, next_seqno, 0.0))
                    next_msg = self.infile.read(500)
                    next_seqno += 1

            if len(msg) != 0 and time.time() - msg[0].timestamp >= self.send_timeout:
                pointer = 0  # 超时时重置pointer

            if pointer < len(msg):  # 当前指针位置未满，可继续发送
                msg_type = 'data'
                if msg[pointer].seqno == 0:
                    msg_type = 'start'
                elif next_msg == "" and len(msg) == 1:
                    msg_type = 'end'

                if self.binaMode:
                    packet = self.make_packet_bina(msg_type, msg[pointer].seqno, msg[pointer].msg)
                    msg[pointer].timestamp = time.time()
                    self.send_bina(packet)
                else:
                    packet = self.make_packet(msg_type, msg[pointer].seqno, msg[pointer].msg)
                    msg[pointer].timestamp = time.time()
                    self.send(packet)

                if self.debug:
                    print("sent seqno: " + str(msg[pointer].seqno))
                pointer += 1

            # 进行ack的接受
            response = self.receive(self.receive_timeout)
            if response is not None:  # 解码response
                response = response.decode()
                self.handle_response(response)

                ack_seqs = response.split('|')[1].split(';')
                ack_seqno = int(ack_seqs[0])
                if self.debug:
                    print("ack_seqs: ", ack_seqs)
                    print("ack_seqno: ", ack_seqno)
                s_acks = []
                if len(ack_seqs) > 1 and len(ack_seqs[1]) > 0:
                    for item in ack_seqs[1].split(','):
                        s_acks.append(int(item))
                newmsg = []
                for item in msg:
                    if item.seqno >= ack_seqno and item.seqno not in s_acks:
                        # 保留所有比ack更大的号码，且没有被捎带确认的
                        newmsg.append(item)
                msg = newmsg
                if pointer < len(msg):
                    pointer_seqno = msg[pointer].seqno
                else:
                    pointer_seqno = next_seqno
                pointer = 0  # 重置pointer，从0开始直到到达待发送位置（发送比pointer指向更大的那个号码）
                while pointer < len(msg) and msg[pointer].seqno < pointer_seqno:
                    pointer += 1
    
        self.infile.close()
    
    def handle_timeout(self):
        pass

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")
        print("-b | --bina Using bina encode message")

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dkb", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False
    binaMode = False
    window_size = 5
    send_timeout = 1
    receive_timeout = 0.1

    for o, a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True
        elif o in ("-b", "--bytes="):
            binaMode = True

    s = Sender(dest, port, filename, debug, sackMode, binaMode, window_size, send_timeout, receive_timeout)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
