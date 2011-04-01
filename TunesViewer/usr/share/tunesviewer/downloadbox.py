import gobject
import gtk
from downloader import Downloader
from common import *

class DownloadBox:
	"""Window for showing and keeping track of downloads"""
	##
	# Holds references to the downloader objects:
	downloaders = []
	downloaded = 0
	total = 0
	lastCompleteDownloads = 0
	
	##
	# Holds the last selected mp3-player directory:
	devicedir = None
	
	##
	# True when a download is running
	downloadrunning = False
	
	def __init__(self,Wopener):
		self.Wopener = Wopener # reference to main prog.
		self.window = gtk.Window()
		self.window.set_icon(self.window.render_icon(gtk.STOCK_SAVE, gtk.ICON_SIZE_BUTTON))
		self.window.set_title("Downloads")
		self.window.set_size_request(500, 200)
		self.window.connect("delete_event",self.onclose)
		self.vbox = gtk.VBox()
		self.vbox.show()
		scrolledwindow = gtk.ScrolledWindow()
		scrolledwindow.show()
		scrolledwindow.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
		scrolledwindow.add_with_viewport(self.vbox)
		self.window.add(scrolledwindow)
		#Window initialized.
	
	##
	# Updates each downloader display.
	def updateLoop(self):
		#Get downloaded/total
		self.downloaded = 0
		self.total = 0
		for i in self.downloaders:
			i.update()
			if i.success:
				self.downloaded += 1
				self.total += 1
			elif i.downloading:
				self.total += 1
		self.updateTitle(self.downloaded,self.total)
		if self.downloaded == self.total:
			self.downloadrunning = False
			self.downloadNotify()
			return False #Downloads Done.
		else:
			return True
	
	##
	# Cancels closing window, hides it instead.
	def onclose(self,widget,data):
		print "hiding downloads"
		self.window.hide()
		return True #Cancel close window.
	
	def cancelAll(self):
		"""Tell all downloaders to cancel"""
		#for i in self.downloaders: (downloaders get removed, can't use for.)
		while len(self.downloaders):
			#print "c",self.downloaders
			self.downloaders[0].cancel(0)

	def updateTitle(self,downloaded,total):
		"""Updates the download window title"""
		self.window.set_title("Downloads (%s/%s downloaded)" % (str(downloaded), str(total)))
	
	def downloadNotify(self):
		print "dlnotify"
		if self.Wopener.config.notifyseconds != 0 and self.lastCompleteDownloads!=self.downloaded:
			self.lastCompleteDownloads = self.downloaded
			try:
				import pynotify
				if (self.total==1):
					s=""
				else:
					s="s"
				pynotify.init("TunesViewer")
				n=pynotify.Notification("Download%s Finished" % s,
					"%s/%s download%s completed successfully." % (self.downloaded, self.total, s),gtk.STOCK_GO_DOWN)
				n.set_timeout(1000*self.Wopener.config.notifyseconds)
				n.show()
			except:
				print "Notification failed"
	
	def newDownload(self,icon,url,localfile,opener):
		"""Downloads a url
		Takes a url, filetype icon, local filename, and opener.
		"""
		#Check if already downloading/downloaded:
		for i in self.downloaders:
			if localfile == i.localfile and (i.downloading or i.success): #already in download-box.
				if (i.downloading):
					message = "File is already downloading."
				elif (i.success):
					message = "File already downloaded."
				msg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
				message)
				msg.run()
				msg.destroy()
				return
		self.window.show()
		d=Downloader(icon,url,localfile,opener,self)
		self.downloaders.append(d)
		#Add the visible downloader progressbar etc.
		el = d.getElement()
		el.show()
		self.vbox.pack_start(el,False,False,10)
		self.window.show()
		if (not(self.downloadrunning)):
			#Start download loop:
			self.downloadrunning = True
			# instead of updating every kb or mb, update regularly.
			# This should work well no matter what the download speed is.
			print "STARTING TIMEOUT"
			#Only update the progress bar only about 4x a second,
			#this won't make cpu work too much.
			gobject.timeout_add(250,self.updateLoop)
		d.start()