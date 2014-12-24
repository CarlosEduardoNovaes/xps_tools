# -*- coding: utf-8 -*-

class XpsBone:
    def __init__(self, id, name, co, parentId):
        self.id = id
        self.name = name
        self.co = co
        self.parentId = parentId

class XpsBonePose:
    def __init__(self, boneName, coordDelta, rotDelta, scale):
        self.boneName = boneName
        self.coordDelta = coordDelta
        self.rotDelta = rotDelta
        self.scale = scale

class XpsMesh:
    def __init__(self, name, textures, vertices, faces, uvCount):
        self.name = name
        self.textures = textures
        self.vertices = vertices
        self.faces = faces
        self.uvCount = uvCount

class XpsVertex:
    def __init__(self, id, co, norm, vColor, uv, boneId, boneWeight):
        self.id = id
        self.co = co
        self.norm = norm
        self.vColor = vColor 
        self.uv = uv
        self.boneId = boneId
        self.boneWeight = boneWeight

class XpsTexture:
    def __init__(self, id, file, uvLayer):
        self.id = id
        self.file = file
        self.uvLayer = uvLayer

class XpsData:
    def __init__(self, header='', bones=[], meshes=[]):
        self.header = header
        self.bones = bones
        self.meshes = meshes

class XpsHeader:
    def __init__(self, magic_number=323232, xps_version=98765, xna_aral='XNAaraL', settingsLen=275, machine='', user='', files='', settings='', pose=''):
        self.magic_number = magic_number
        self.xps_version = xps_version
        self.xna_aral = xna_aral
        self.settingsLen = settingsLen
        self.machine = machine
        self.user = user
        self.files = files
        self.settings = settings
        self.pose = pose

