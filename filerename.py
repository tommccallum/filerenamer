import json
import shutil
import os
import sys

class Config:
  def __init__(self):
    self.remove = [ ":" ]
    self.replace = { "(":"- " }
    self.testMode = True

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
  for ch in config.remove:
    text = text.replace(ch, "")
  for ch in config.replace:
    text = text.replace(ch, config.replace[ch])
  return text

def renameDirectory(config, path):
  """
  Rename the directory and its subdirectories
  """
  if not os.path.isdir(path):
    raise RuntimeError("directory {} does not exist".format(path))
  newPath = renameString(config, path)
  if newPath != path:
    if config.testMode:
      if path != newPath:
        print("[dir] Transform {} => {}".format(path, newPath))
    else:
      if path != newPath:
        print("[dir] Transform {} => {}".format(path, newPath))
        shutil.move(path, newPath)

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
        renameAudioFile(config, filePath)
      elif ext == ".m3u":
        renameM3u(config, filePath)
      else:
        raise ValueError("invalid file {} found with extension {}".format(filePath, ext))

def renameAudioFile(config, path):
  """
  Rename the audio file
  """
  if not os.path.isfile(path):
    raise RuntimeError("file {} does not exist".format(path))
  dirNamePart = os.path.dirname(path)
  fileNamePart = os.path.basename(path)
  newFileNamePath = renameString(config, fileNamePart)
  newPath = os.path.join(dirNamePart, newFileNamePath)
  if config.testMode:
    if path != newPath:
      print("[mp3] Transform {} => {}".format(path, newPath))
  else:
    if path != newPath:
      print("[mp3] Transform {} => {}".format(path, newPath))
      shutil.move(path, newPath)

def renameM3u(config, path):
  """
  Rename the m3u file itself and also the contents
  """
  if not os.path.isfile(path):
    raise RuntimeError("file {} does not exist".format(path))
  dirNamePart = os.path.dirname(path)
  fileNamePart = os.path.basename(path)
  newFileNamePath = renameString(config, fileNamePart)
  newPath = os.path.join(dirNamePart, newFileNamePath)
  
  newContents = []
  with open(path, "r") as inFile:
    contents = inFile.readlines()
    for l in contents:
      newl = renameString(config, l.strip())
      newContents.append(newl + "\n")
  
  
  for ii, cc in enumerate(contents):
    if cc != newContents[ii]:
      print("[m3u] Transform {} => {}".format(cc.strip(), newContents[ii].strip()))

  if not config.testMode:
    with open(newPath, "w") as outFile:
      outFile.writelines(newContents)
    print("[m3u] Deleting {}".format(path))
    os.remove(path)


if __name__ == "__main__":
  configFilePath = None
  testMode = True
  ii=1;
  while ii < len(sys.argv)-1:
    if sys.argv[ii] == "-c":
      configFilePath = sys.argv[ii+1]
      ii += 1
    elif sys.argv[ii] == "--force":
      testMode = False
    else:
      raise ValueError("invalid argument {}".format(sys.argv[ii]))
    ii+= 1
  targetPath = sys.argv[len(sys.argv)-1]
  config = createConfig(configFilePath)
  config.testMode = testMode
  if os.path.isdir(targetPath):
    renameDirectory(config, targetPath)
  elif os.path.isfile(targetPath):
    _, ext = os.path.splitext(targetPath)
    if ext == ".mp3":
      renameAudioFile(config, targetPath)
    elif ext == ".m3u":
      renameM3u(config, targetPath)
    else:
      raise ValueError("File is not a m3u or an mp3 file")
  else:
    raise ValueError("{} is not a valid directory or file".format(targetPath))
