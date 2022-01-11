import json
import shutil
import os
import sys
import re

GLOBAL_EXTENSIONS_TO_IGNORE=[".iso"]

class Config:
  def __init__(self):
    self.remove = [ ":" ]
    self.replace = { "(":"- " }
    self.testMode = True
    self.makeM3u = False
    self.editMetaTags = False

def createConfig(file=None):
  config = Config()
  if file:
    with open(file, "r") as infile:
      data = json.load(infile)
    if "remove" in data:
      config.remove = data["remove"]
    if "replace" in data:
      config.replace = data["replace"]
  return config

def renameString(config, text):
  if text.startswith("#EXT"):
    return text
  # we replace first and then remove so that if the replacement
  # adds in an illegal character then we can remove it
  for ch in config.replace:
    text = text.replace(ch, config.replace[ch])
  for ch in config.remove:
    text = text.replace(ch, "")
  ## collapse multiple spaces
  multiple_spaces = re.compile(r"\s+")
  text = multiple_spaces.sub(" ", text)
  text = text.strip()
  return text

def renameDirectory(config, path, renameThisDirectory=True):
  """
  Rename the directory and its subdirectories
  """
  print("[ENTER] {}".format(path))
  if not os.path.isdir(path):
    raise RuntimeError("directory {} does not exist".format(path))

  if renameThisDirectory:
    print("[RENAME] Directory: {}".format(path))
    lastDirName = os.path.basename(path)
    dirPath = os.path.dirname(path)
    newLastDirName = renameString(config, lastDirName)
    newPath = os.path.join(dirPath, newLastDirName)
    if newPath != path:
      if config.testMode:
        if path != newPath:
          print("[dir] Transform {} => {}".format(path, newPath))
      else:
        if path != newPath:
          print("[dir] Transform {} => {}".format(path, newPath))
          if os.path.isdir(newPath):
            raise ValueError("[Rename failed] Attempted to transform {} to {} but it already exists".format(path, newPath))
          shutil.move(path, newPath)
  else:
    newPath = path

  targetPath = newPath
  if config.testMode:
    # we need to do this as we will not have actually changed the path
    # to the newPath
    targetPath = path

  for root,d_names,f_names in os.walk(targetPath):
    for d in d_names:
      dirPath = os.path.join(root,d)
      renameDirectory(config, dirPath)
  
  for root,d_names,f_names in os.walk(targetPath):
    for f in f_names:
      filePath = os.path.join(root, f)
      _, ext = os.path.splitext(filePath)
      if ext == ".mp3":
        renameFile(config, filePath)
      elif ext == ".m3u":
        renameM3u(config, filePath)
      elif ext == ".mp4" or ext == ".m4v":
        renameFile(config, filePath)
      elif ext in GLOBAL_EXTENSIONS_TO_IGNORE:
        # ignore iso files as they are ripped dvds most likely
        pass
      else:
        raise ValueError("invalid file {} found with extension {}".format(filePath, ext))

  if config.makeM3u:
    for root,d_names,f_names in os.walk(targetPath):
      for d in d_names:
        dirPath = os.path.join(root,d)
        makeM3UFile(config, dirPath)

  if config.editMetaTags:
    for root,d_names,f_names in os.walk(targetPath):
      for d in d_names:
        dirPath = os.path.join(root,d)
        modifyMetaTags(config, dirPath)

def makeM3UFile(config, path):
  if os.path.isdir(path) == False:
    raise ValueError("{} must be a directory to make M3u file from".format(path))
  dirName = os.path.basename(path)
  dirPath = os.path.dirname(path)
  m3uFileName = dirName.strip() + ".m3u"
  m3uPath = os.path.join(dirPath, m3uFileName)
  if os.path.isfile(m3uPath):
    return
  
  print("[m3u] Creating {}".format(m3uPath))
  if config.testMode == False:
    lines = []
    for root,d_names,f_names in os.walk(path):
      for f in sorted(f_names):
        _, fileExt = os.path.splitext(f)
        if fileExt == ".mp3":
          filePath = os.path.join(dirName, f)
          lines.append(filePath)

    if len(lines) > 0:
      lines = map( lambda x : x + '\n', lines)

      dirName = os.path.basename(path)
      dirPath = os.path.dirname(path)
      m3uFileName = dirName.strip() + ".m3u"
      m3uPath = os.path.join(dirPath, m3uFileName)
      with open(m3uPath,"w") as outFile:
        outFile.writelines(lines)


def renameFile(config, path):
  """
  Rename the file
  """
  if not os.path.isfile(path):
    raise RuntimeError("file {} does not exist".format(path))
  dirNamePart = os.path.dirname(path)
  fileNamePart = os.path.basename(path)
  fileNameFirst, ext = os.path.splitext(fileNamePart)
  newFileNameFirst = renameString(config, fileNameFirst)
  newFileNamePath = newFileNameFirst + ext
  newPath = os.path.join(dirNamePart, newFileNamePath)
  if config.testMode:
    if path != newPath:
      print("[file] Transform {} => {}".format(path, newPath))
  else:
    if path != newPath:
      print("[file] Transform {} => {}".format(path, newPath))
      if os.path.isdir(newPath):
          raise ValueError("[Move failed] Attempted to transform {} to {} but it already exists".format(path, newPath))
      shutil.move(path, newPath)

def renameM3u(config, path):
  """
  Rename the m3u file itself and also the contents
  """
  print("[Rename M3U List] {}".format(path))
  _, ext = os.path.splitext(path)
  if ext != ".m3u":
    raise RuntimeError("{} is not an m3u file".format(path))
  if not os.path.isfile(path):
    raise RuntimeError("file {} does not exist".format(path))
  dirNamePart = os.path.dirname(path)
  fileNamePart = os.path.basename(path)
  fileNameFirst, ext = os.path.splitext(fileNamePart)
  newFileNameFirst = renameString(config, fileNameFirst)
  newFileNamePath = newFileNameFirst + ext
  
  newPath = os.path.join(dirNamePart, newFileNamePath)
  
  newContents = []
  with open(path, "r") as inFile:
    contents = inFile.readlines()
    for l in contents:
      xpath = l.strip()
      if xpath.startswith("#"):
        newContents.append(xpath + "\n")
      else:  
        d = os.path.dirname(xpath)
        base = os.path.basename(xpath)
        file, ext = os.path.splitext(base)
        newl = renameString(config, file)
        newl = os.path.join(d,newl + ext)
        # if not os.path.isfile(newl) and not config.testMode :
        #   raise RuntimeError("{} => {}, transformed file does not exist".format(path, newl))
        newContents.append(newl + "\n")
  
  
  for ii, cc in enumerate(contents):
    if cc != newContents[ii]:
      print("[m3u] Transform {} => {}".format(cc.strip(), newContents[ii].strip()))

  if not config.testMode:
    with open(newPath, "w") as outFile:
      outFile.writelines(newContents)
    if newPath != path:
      if os.path.isfile(path):
        print("[m3u] Deleting {}".format(path))
        os.remove(path)

def checkCapitalisation(x):
  """
  We don't want common words such as these capitalised e.g. First in a title
  """
  words = ['the', 'a', 'of', 'some', 'and', 'or', 'in', 'at', 'all']
  if x.lower() in words:
    return x.lower()
  return x

def modifyMetaTags(config, path):
  if os.path.isdir(path) == False:
    raise ValueError("{} must be a directory".format(path))
  dirName = os.path.basename(path)
  dirPath = os.path.dirname(path)
  
  for root,d_names,f_names in os.walk(path):
    for f in sorted(f_names):
      filePath = os.path.join(path, f)
      fileName, fileExt = os.path.splitext(f)
      if fileExt == ".mp4" or fileExt == ".m4v":
        print("[metadata] Modifying {}".format(filePath))
        fileName = fileName.replace("_", " ")
        if fileName.isupper() or fileName.islower():
          fileName = fileName.capitalize()
        parts = fileName.split("-")
        if len(parts) == 1:
          album = ""
          title = parts[0]
        else:
          parts = [ x.strip() for x in parts ]
          parts = [ checkCapitalisation(x) for x in parts ]
          album = parts[0].strip()
          title = ' - '.join(parts[1:])
        outFilePath = "{}.tmp{}".format(filePath, fileExt)
        cmd = "ffmpeg -i \"{}\" -metadata title=\"{}\" -metadata album=\"{}\" -codec copy \"{}\"".format(filePath, title, album, outFilePath)
        print("[metadata] album={} title={}".format(album, title))
        print("[ffmpeg] {}".format(cmd))
        if config.testMode == False:
          os.system(cmd)
          if os.path.getsize(outFilePath) > 0:
            shutil.copyfile(outFilePath, filePath)
            os.remove(outFilePath)
          else:
            raise RuntimeError("Modified file {} was zero length.\nFFmpeg command executed was:\n'{}'".format(outFilePath, cmd))

if __name__ == "__main__":
  configFilePath = None
  testMode = True
  makeM3u = False
  editMetaTags = False
  ii=1;
  while ii < len(sys.argv)-1:
    if sys.argv[ii] == "-c":
      configFilePath = sys.argv[ii+1]
      ii += 1
    elif sys.argv[ii] == "--force":
      testMode = False
    elif sys.argv[ii] == "--make-m3u":
      makeM3u = True
    elif sys.argv[ii] == "--edit-meta-tag" or sys.argv[ii] == "--edit-meta-tags":
      editMetaTags = True
    else:
      raise ValueError("invalid argument {}".format(sys.argv[ii]))
    ii+= 1
  targetPath = sys.argv[len(sys.argv)-1]
  config = createConfig(configFilePath)
  config.testMode = testMode
  config.makeM3u = makeM3u
  config.editMetaTags = editMetaTags
  if os.path.isdir(targetPath):
    # run a check on numbers of files and directories
    dirCount = 0
    fileExts = {}
    for root,d_names,f_names in os.walk(targetPath):
      for d in d_names:
        dirCount += 1
      for f in f_names:
        _, ext  = os.path.splitext(f)
        if ext not in fileExts:
          fileExts[ext] = 1
        else:
          fileExts[ext] += 1
    print("Directories: {}".format(dirCount))
    for e in fileExts.keys():
      print("{}: {}".format(e, fileExts[e]))
    
    renameDirectory(config, targetPath, False)

    newDirCount = 0
    newFileExts = {}
    for root,d_names,f_names in os.walk(targetPath):
      for d in d_names:
        newDirCount += 1
      for f in f_names:
        _, ext  = os.path.splitext(f)
        if ext not in newFileExts:
          newFileExts[ext] = 1
        else:
          newFileExts[ext] += 1
    print("Directories: {}".format(newDirCount))
    for e in newFileExts.keys():
      print("{}: {}".format(e, newFileExts[e]))
    
    for e in fileExts:
      if fileExts[e] != newFileExts[e]:
        raise RuntimeError("Lost music: {} => {}".format(fileExts[e], newFileExts[e]))
    if newDirCount != dirCount:
      raise RuntimeError("Lost directory: {} => {}".format(dirCount, newDirCount))

  elif os.path.isfile(targetPath):
    _, ext = os.path.splitext(targetPath)
    if ext == ".mp3":
      renameFile(config, targetPath)
    elif ext == ".m3u":
      renameM3u(config, targetPath)
    else:
      raise ValueError("File is not a m3u or an mp3 file")
  else:
    raise ValueError("{} is not a valid directory or file".format(targetPath))
