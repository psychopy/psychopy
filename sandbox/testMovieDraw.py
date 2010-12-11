


import sys, thread, time, traceback, Queue, os

import pymedia
import pymedia.muxer as muxer
import pymedia.audio.acodec as acodec
import pymedia.video.vcodec as vcodec
import pymedia.audio.sound as sound

if os.environ.has_key( 'PYCAR_DISPLAY' ) and os.environ[ 'PYCAR_DISPLAY' ]== 'directfb':
  import pydfb as pygame
  YV12= pygame.PF_YV12
else:
  import pygame
  YV12= pygame.YV12_OVERLAY

SEEK_SEC= 10
SEEK_IN_PROGRESS= -1

########################################################################3
# Simple video player 
class VPlayer:
  # ------------------------------------

  def __init__( self ):
    self.frameNum= -1
    self.exitFlag= 1
    self.ct= None
    self.pictureSize= None
    self.paused= 0
    self.snd= None
    self.stopPlayback()
    self.err= []
    self.aDelta= 0
    self.aBitRate= 0
    self.vBitRate= 0
    self.seek= 0
    self.vc= None
    self.ac= None
  
  # ------------------------------------

  def resetAudio( self ):
    # No delta for audio so far

    self.snd= self.resampler= None
    self.aDelta= 0
    self.aDecodedFrames= []
    if self.ac:
      self.ac.reset()
  
  # ------------------------------------

  def initAudio( self, params ):
    try:
      # Reset audio stream

      self.resetAudio()
      # Initializing audio codec

      self.ac= acodec.Decoder( params )
    except:
      traceback.print_exc()
      self.err.append( sys.exc_info()[1] )
  
  # ------------------------------------

  def resetVideo( self ):
    # Init all used vars first

    self.decodeTime= self.vBitRate= self.frameNum= \
    self.sndDelay= self.hurry= self.videoPTS= \
    self.lastPTS= self.frRate= self.vDelay= 0
    self.seek= 0
    if self.initADelta!= -1:
      self.seekADelta= self.initADelta
    
    # Zeroing out decoded pics queue

    self.decodedFrames= []
    self.rawFrames= []
    if self.vc:
      self.vc.reset()
  
  # ------------------------------------

  def initVideo( self, params ):
    # There is no overlay created yet

    self.overlay= self.pictureSize= None
    try:
      # Set the initial sound delay to 0 for now

      # It defines initial offset from video in the beginning of the stream

      self.initADelta= -1
      self.resetVideo()
      self.seekADelta= 0
      # Setting up the HW video codec

      self.vc= pymedia.video.ext_codecs.Decoder( params ) 
    except:
      try:
        # Fall back to SW video codec

        self.vc= vcodec.Decoder( params )
      except:
        traceback.print_exc()
        self.err.append( sys.exc_info()[1] )
  
  # ------------------------------------

  def createOverlay( self, vfr ):
    # Create overlay if any

    self.overlay= pygame.Overlay( YV12, vfr.size )
    # Save real picture size

    if vfr.aspect_ratio> .0:
      self.pictureSize= ( vfr.size[ 1 ]* vfr.aspect_ratio, vfr.size[ 1 ] )
    else:
      self.pictureSize= vfr.size
    # Locate overlay on the screen

    self.setOverlay( self.overlayLoc )
  
  # ------------------------------------

  def processVideoFrame( self, d ):
    # See if we should show video frame now

    self.rawFrames.append( d )
    if len( self.decodedFrames )== 0:
      if self.decodeVideoFrame()== -1:
        return
    
    # See if we have our frame inline with the sound

    while 1:
      if len( self.decodedFrames )== 0:
        return
      
      vfr, videoPTS= self.decodedFrames[ 0 ]
      self.vDelay= videoPTS- self.seekADelta- self.getPTS()
      frRate= float( vfr.rate_base )/ vfr.rate
      res= self.decodeVideoFrame()
      if res== -1 or ( res== -2 and self.vDelay> 0 ) or ( self.snd and self.snd.getLeft()< frRate ):
        return
      
      # If delay

      print '!!', self.vDelay, self.frameNum, videoPTS, self.getPTS(), len( self.decodedFrames ), len( self.rawFrames ), self.snd.getLeft()
      if self.vDelay< frRate / 4:
        # Remove frame from the queue

        del( self.decodedFrames[ 0 ] )
        
        # Get delay for seeking

        if self.frameNum== 0 and self.initADelta== -1:
          self.initADelta= self.snd.getLeft() #+ self.snd.getPosition()

          #self.aDelta= -self.snd.getPosition()

        
        # Increase number of frames

        self.frameNum+= 1
        
        # Skip frame if no data inside, but assume it was a valid frame though

        if vfr.data:
          if self.overlayLoc and self.overlay== None:
            self.createOverlay( vfr )
          
          # Set data for the overlay

          self.overlay.set_data( vfr.data )
          # Display it

          self.overlay.display()
          self.vDelay= frRate
          #break

      elif self.vDelay> 0 and self.vDelay< frRate and len( self.rawFrames )== 0:
        time.sleep( self.vDelay )
    
  # ------------------------------------

  def decodeVideoFrame( self ):
    # Decode the video frame

    if self.snd== None and self.seek!= SEEK_IN_PROGRESS :
      return -1
    
    while len( self.rawFrames ):
      d= self.rawFrames.pop( 0 )
      vfr= self.vc.decode( d[ 1 ] )
      if vfr:
        if self.seek== SEEK_IN_PROGRESS:
          if vfr.data:
            self.seek= 0
          else:
            return 0
        
        # If frame has data in it, put it in to the queue along with PTS

        self.decodedFrames.append( ( vfr, self.videoPTS ) )
        # Set up the video bitrate for the informational purpose

        if self.vBitRate== 0:
          self.vBitRate= vfr.bitrate
          
        # Handle the PTS

        rate= float( vfr.rate_base )/ vfr.rate
        if d[ 3 ]> 0 and self.lastPTS< d[3]:
          # Get the first lowest PTS( we do not have DTS :( )

          self.lastPTS= d[3]
          self.videoPTS= float( d[ 3 ] ) / 90000
          #print 'VPTS:', self.videoPTS, vfr.pict_type
        else:
          # We cannot accept PTS, just calculate it

          self.videoPTS+= rate
        
        return 0
    
    return -2
  
  # ------------------------------------

  def processAudioFrame( self, d ):
    # Decode audio frame

    afr= self.ac.decode( d[ 1 ] )
    if afr:
      # See if we set up the sound

      if self.snd== None:
        self.aBitRate= afr.bitrate
        #print 'Sound: ', afr.sample_rate, afr.channels, afr.bitrate 
        try:
          # Hardcoded S16 ( 16 bit signed ) for now

          self.snd= sound.Output( afr.sample_rate, afr.channels, sound.AFMT_S16_LE )
          self.resampler= None
        except:
          try:
            # Create a resampler when no multichannel sound is available

            self.resampler= sound.Resampler( (afr.sample_rate,afr.channels), (afr.sample_rate,2) )
            # Fallback to 2 channels

            self.snd= sound.Output( afr.sample_rate, 2, sound.AFMT_S16_LE )
          except:
            traceback.print_exc()
            self.err.append( sys.exc_info()[1] )
            return
      
      # See if we need to resample the audio data

      s= afr.data
      if self.resampler:
        s= self.resampler.resample( s )
      
      # Handle the PTS accordingly

      if d[ 3 ]> 0 and self.aDelta== 0:
        # set correction factor in case of PTS presence

        self.aDelta= ( float( d[ 3 ] ) / 90000 )- self.snd.getPosition()- self.snd.getLeft()
      
      # Play the raw data if we have it

      if len( s )> 0:
        self.aDecodedFrames.append( s )
        while len( self.aDecodedFrames ):
          # See if we can play sound chunk without clashing with the video frame

          if len( s )> self.snd.getSpace():
            break
          
          #print 'LEFT:', self.snd.getLeft(), len( s ), self.snd.getSpace()
          self.snd.play( self.aDecodedFrames.pop(0) )
  
  # ------------------------------------

  def start( self ):
    if self.ct:
        raise 'cannot run another copy of vplayer'
    self.exitFlag= 0
    self.ct= thread.start_new_thread( self.readerLoop, () )
  
  # ------------------------------------

  def stop( self ):
    # Stop if anything is playing now

    self.stopPlayback()
    # Turn the flag to exist the main thread

    self.exitFlag= 1
  
  # ------------------------------------

  def startPlayback( self, file ):
    # Stop if anything is playing now

    self.stopPlayback()
    # Set the new file for playing

    self.playingFile= file
  
  # ------------------------------------

  def stopPlayback( self, bForce= True ):
    # Close the overlay

    self.setOverlay( None )
    self.playingFile= None
    # Unpause playback if any

    self.paused= 0
  
  # ------------------------------------

  def seekRelative( self, secs ):
    while self.seek:
      time.sleep( 0.01 )
    
    self.seek= secs* 1000000
  
  # ------------------------------------

  def setOverlay( self, loc ):
    self.overlayLoc= loc
    if loc== None:
      self.overlay= None
    elif self.overlay:
      # Calc the scaling factor

      sw,sh= self.overlayLoc[ 2: ]
      w,h= self.pictureSize
      x,y= self.overlayLoc[ :2 ]
      factor= min( float(sw)/float(w), float(sh)/float(h) )
      # Find appropriate x or y pos

      x= ( sw- factor* w ) / 2+ x
      y= ( sh- factor* h ) / 2+ y
      self.overlay.set_location( (int(x),int(y),int(float(w)*factor),int(float(h)*factor)) )
      
  # ------------------------------------

  def isPlaying( self ):
    return self.overlay!= None
  
  # ------------------------------------

  def getPTS( self ):
    if self.snd== None:
        return 0
    return self.snd.getPosition()+ self.aDelta
  
  # ------------------------------------

  def readerLoop( self ):
    """
    """
    print 'Main video loop has started.'
    f= None
    try:
      while self.exitFlag== 0:
        if self.playingFile== None:
          time.sleep( 0.01 )
          continue
        
        self.frameNum= -1
        
        # Initialize demuxer and read small portion of the file to have more info on the format

        format= menu.cache.getExtension( self.playingFile )
        dm= muxer.Demuxer( format )
        f= menu.cache.open( self.playingFile )
        s= f.read( 300000 )
        r= dm.parse( s )
        print dm.streams
        
        # Setup video( only first matching stream will be used )

        self.err= []
        for vindex in xrange( len( dm.streams )):
          if dm.streams[ vindex ][ 'type' ]== muxer.CODEC_TYPE_VIDEO:
            self.initVideo( dm.streams[ vindex ] )
            break
        
        # Setup audio( only first matching stream will be used )

        for aindex in xrange( len( dm.streams )):
          if dm.streams[ aindex ][ 'type' ]== muxer.CODEC_TYPE_AUDIO:
            self.initAudio( dm.streams[ aindex ] )
            break
        
        # Open current file for playing

        currentFile= menu.cache.getPathName( self.playingFile )
        
        # Play until no exit flag, not eof, no errs and file still the same

        while len(s) and len( self.err )== 0 and \
            self.exitFlag== 0 and self.playingFile and \
            menu.cache.getPathName( self.playingFile )== currentFile:
          for d in r:
            # Seeking stuff

            if not self.seek in ( 0, SEEK_IN_PROGRESS ):
              f.seek( self.seek, 1 )
              self.resetAudio()
              self.resetVideo()
              self.rawFrames= []
              self.decodedFrames= []
              self.seek= SEEK_IN_PROGRESS
              break
            
            try:
              # Demux file into streams

              if d[ 0 ]== vindex:
                #print 'V',
                # Process video frame

                self.processVideoFrame( d )
              elif d[ 0 ]== aindex and self.seek!= SEEK_IN_PROGRESS:
                #print 'A',
                # Decode and play audio frame

                self.processAudioFrame( d )
            except:
              traceback.print_exc()
              raise
          
          # Read next encoded chunk and demux it

          s= f.read( 10000 )
          r= dm.parse( s )
        
        if f: f.close()
        # Close current file when error detected

        if len( self.err ) or len( s )== 0:
          self.stopPlayback( False )
          self.playingFile= None
    finally:
      self.stopVideo()
      self.stopAudio()
      print 'Main video loop has closed.'

player= VPlayer()

if __name__ == "__main__":
  ########################################################################3

  # Simple cache replacer for standalone testing

  class Menu:
    NAME_KEY= 'name'
    class Cache:
      def open( self, f ):
        return open( f['name'], 'rb' )
      def getPathName( self, f ):
        return f[ 'name' ]
      def getExtension( self, f ):
        return f[ 'name' ].split( '.' )[ -1 ].lower()
    
    cache= Cache()
  
  # Menu module instance for standalone testing

  menu= Menu()
  
  if len( sys.argv )< 2 or len( sys.argv )> 3:
      print 'Usage: vplayer <file_name>'
  else:
      pygame.init()
      pygame.display.set_mode( (800,600), 0 )
      player.startPlayback( { 'name': sys.argv[ 1 ] } )
      player.start()
      player.setOverlay( (0,0,800,600) )
      while player.isPlaying()== 0:
          time.sleep( .05 )
      while player.isPlaying():
        e= pygame.event.wait()
        if e.type== pygame.KEYDOWN: 
            if e.key== pygame.K_ESCAPE: 
                player.stopPlayback()
                break
            if e.key== pygame.K_RIGHT: 
                player.seekRelative( SEEK_SEC )
            if e.key== pygame.K_LEFT: 
                player.seekRelative( -SEEK_SEC )
else:
  from pycar import menu

"""
./ffmpeg -i /home/bors/Forrest.Gump\(\ DVDRip.DivX\ \).CD2.avi -vn -ar 48000 -ab 128 test.mp3
"""

