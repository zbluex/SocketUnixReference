#!/usr/bin/env python
import commands
import time
import os
import re
import argparse
import sys


def logerror(handler, errcode):
	if errcode > 0:
		print("[ERROR]%s failed, Error Code: %s\n") % (handler, os.strerror(errcode))
		exit(1)


class IPCRef(object):
	# define CONST
	__netstatTcpUdpCmd = "netstat -atunp|grep -v '-'"
	__netstatUnixCmd = "netstat -axnp"
	__unixInfoCmd = "ss -xp|grep -v Netid"
	#define variable
	tcpUdpListenMap = dict()
	tcpUdpEstablishedListData = list()
	unixListenMap = dict()
	unixPathMap = dict()
	unixPearPortMap = dict()

	def calculate_socket_reference(self):
		self.get_tcpudp_info()
		for l in self.tcpUdpEstablishedListData:
					if self.tcpUdpListenMap.has_key(l[4]):
							if  self.tcpUdpListenMap[l[4]][1].has_key(l[-1]):
								self.tcpUdpListenMap[l[4]][1][l[-1]] = self.tcpUdpListenMap[l[4]][1][l[-1]] + 1
							else:
								self.tcpUdpListenMap[l[4]][1][l[-1]] = 1

	def get_tcpudp_info(self):
		self.tcpUdpEstablishedListData = list()

		netinfo = commands.getstatusoutput(self.__netstatTcpUdpCmd)
		logerror("Get socket information", netinfo[0])
		netinfo = netinfo[1].split('\n')
		listenList = list()
		establishedList = list()
		for l in netinfo:
			if l.find('LISTEN') >= 0 or l.find('0.0.0.0:*') >= 0 or l.find(':::*') >= 0:
				listenList.append(l)
			else:
				establishedList.append(l)

		for l in listenList:
			info = l.split()
			if not self.tcpUdpListenMap.has_key(info[3]):
				self.tcpUdpListenMap[info[3]] = list()
				self.tcpUdpListenMap[info[3]].append(info[-1])
				self.tcpUdpListenMap[info[3]].append(dict())

		for l in establishedList:
			self.tcpUdpEstablishedListData.append(l.split())

	def get_unix_info(self):
		self.unixPathMap.clear()
		self.unixPearPortMap.clear()

		netinfo = commands.getstatusoutput(self.__netstatUnixCmd)
		logerror("Get socket information", netinfo[0])
		netinfo = netinfo[1].split('\n')
		for l in netinfo:
			e = l.split()
			if l.find('LISTEN') >= 0 and e[-2] != '-' :
				if not self.unixListenMap.has_key(e[-1]):
					self.unixListenMap[e[-1]] = list()
					self.unixListenMap[e[-1]].append(e[-2])
					self.unixListenMap[e[-1]].append(dict())
		netinfo = commands.getstatusoutput(self.__unixInfoCmd)
		logerror("Get unix information", netinfo[0])
		netinfo = netinfo[1].split('\n')
		for l in netinfo:
			e = l.split()
			ll = e[0:8]
			if "".join(e[8:]) != "":
				ll.append("".join(e[8:]))
			if e[4] != '*':
				if not self.unixPathMap.has_key(ll[4]):
					self.unixPathMap[ll[4]] = list()
				self.unixPathMap[ll[4]].append(ll)
			self.unixPearPortMap[ll[5]] = ll

	def calculate_unix_reference(self):
		self.get_unix_info()
		for k in self.unixListenMap.keys():
			if self.unixPathMap.has_key(k):
				for l in self.unixPathMap[k]:
					if self.unixPearPortMap.has_key(l[7]) and len(self.unixPearPortMap[l[7]]) >= 9:
						#format convert from ['users', 'xxxx'] to 'xxxx'
						names = re.split(':',self.unixPearPortMap[l[7]][-1])[1]
						print names
						#format convert form '((xxxx),(xxxx))' to 'xxxx),(xxxx'
						names = re.split('\),\(',names[2:-2])
						print names
						for name in names:
							name = name.split(',')
							key = name[1] + "/" + name[0].split("\"")[1]
							if self.unixListenMap[k][1].has_key(key):
								self.unixListenMap[k][1][key] = self.unixListenMap[k][1][key] + 1
							else:
								self.unixListenMap[k][1][key] = 1

	def calculate_reference(self):
		self.calculate_socket_reference()
		self.calculate_unix_reference()


def get_parser():
	# parse args
	parser = argparse.ArgumentParser(
		description="Socket and Unix Reference analyze tool;",
		epilog="author: zhuqi zbluex@gmail.com",
		version="1.0.0"
	)
	parser.add_argument("-t", "--time", dest="time",
						help="analyze consistence time, second",
						default="1",
						metavar="int")

	return parser


def args_handler(args):
	global timeout
	if int(args.time) > 0:
		timeout = int(args.time)

	return


if __name__ == "__main__":
	timeout = 1

	g_parser = get_parser()
	args_handler(g_parser.parse_args())

	ipc_ref = IPCRef()
	while timeout > 0:
		ipc_ref.calculate_reference()
		timeout = timeout - 1
		if timeout > 0:
			time.sleep(1)

	print("Local Socket Reference:")
	for k,v in ipc_ref.tcpUdpListenMap.items():
		print k,v

	print("")
	print("Unix Reference:")
	for k,v in ipc_ref.unixListenMap.items():
		print k,v

