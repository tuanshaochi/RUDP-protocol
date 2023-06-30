# RUDP-protocol
A stimulation of transfer protocal

<br>

## 1.实现GBN和选择重传

代码以及测试都将被实际执行进行验证，请务必按如下格式保证代码和测试可执行：

Go-Back-N接收端：python Receiver.py

Go-Back-N发送端：python Sender.py -f <file name>

选择重传接收端：python Receiver.py -k

选择重传发送端：python Sender.py -f <file name> -k

测试：python TestHarness.py -s Sender.py -r Receiver.py

<br>

## 2.有传输字符文件和二进制文件。添加-b即可传输图片和视频。

checksum校验函数在遇到bina模式时需要重写


<br>

## 3.对于GBN和选择重传，使用丢包测试通过。自己编写的失序、重复均通过。
