# -*- coding: utf-8 -*-

from XNALaraMesh import write_ascii_xps
from XNALaraMesh import write_bin_xps
from XNALaraMesh import xps_types
from XNALaraMesh import mock_xps_data
from XNALaraMesh import export_xnalara_pose

import timeit
import time
import bpy
#import math
import mathutils

import os


from mathutils import *

#imported XPS directory
rootDir = ''
def coordTransform(coords):
    x, y, z = coords
    y = -y
    return (x, z, y)

def faceTransform(face):
    return [face[0],face[2],face[1]]

def faceTransformList(faces):
    transformed = [faceTransform(face) for face in faces]
    return transformed

def uvTransform(uv):
    u = uv[0] - uvDisplX
    v = uvDisplY - uv[1]
    return [u, v]

def rangeFloatToByte(float):
    return int(float * 255)%256

def rangeByteToFloat(byte):
    return float/255

def uvTransformLayers(uvLayers):
    return [uvTransform(uv) for uv in uvLayers]

def getArmature():
    selected_obj = bpy.context.selected_objects
    armature_obj = next((obj for obj in selected_obj if obj.type == 'ARMATURE'), None)
    return armature_obj

def fillArray(array, maxLen, value):
    #Complete the array with value and limits to maxLen
    filled = array + [value]*(maxLen - len(array))
    return filled[:maxLen]

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('%s function took %0.3f ms' % (f.__name__, (time2-time1)*1000.0))
        return ret
    return wrap

def getOutputFilename(filename, uvX, uvY, impSelected, exportPose):
    global uvDisplX
    global uvDisplY
    global importSelected
    global expDefPose
    uvDisplX = uvX
    uvDisplY = uvY
    importSelected = impSelected
    expDefPose = exportPose

    blenderExportSetup()
    xpsExport(filename)
    blenderExportFinalize()

def blenderExportSetup():
    # switch to object mode and deselect all
    objectMode()

def blenderExportFinalize():
    pass

def objectMode():
    current_mode = bpy.context.mode
    if bpy.context.scene.objects.active and current_mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

def saveXpsFile(filename, xpsData):
    dirpath, file = os.path.split(filename)
    basename, ext = os.path.splitext(file)
    if ext in ('.mesh', '.xps'):
        write_bin_xps.writeXpsModel(filename, xpsData)
    elif ext in('.ascii'):
        write_ascii_xps.writeXpsModel(filename, xpsData)

@timing
def xpsExport(filename):
    global rootDir
    global xpsData
    global importSelected
    importSlected = True

    print ("------------------------------------------------------------")
    print ("---------------EXECUTING XPS PYTHON EXPORTER----------------")
    print ("------------------------------------------------------------")
    print ("Exporting file: ", filename)

    if importSelected:
        exportObjects = bpy.context.selected_objects
    else:
        exportObjects = bpy.context.scene.objects

    armature, meshes = exportSelected(exportObjects)

    xpsBones = exportArmature(armature)
    xpsMeshes = exportMeshes(meshes)

    poseString = ''
    if(expDefPose):
        xpsPoseData = export_xnalara_pose.xpsPoseData(armature)
        poseString = write_ascii_xps.writePose(xpsPoseData).read()

    header = mock_xps_data.buildHeader(poseString)
    xpsData = xps_types.XpsData(header=header, bones=xpsBones, meshes=xpsMeshes)

    saveXpsFile(filename, xpsData)

def exportSelected(objects):
    meshes = []
    armatures = []
    for object in objects:
        if object.type == 'ARMATURE':
            armatures.append(object)
        elif object.type == 'MESH':
            meshes.append(object)
    armature = getArmature()
    return armature, meshes

def exportArmature(armature):
    xpsBones = []
    if armature:
        bones = armature.data.bones
        print('Exporting Armature', len(bones), 'Bones')
        #activebones = [bone for bone in bones if bone.layers[0]]
        activebones = bones
        for bone in activebones:
            objectMatrix = armature.matrix_local
            id = bones.find(bone.name)
            name = bone.name
            co = coordTransform(objectMatrix * bone.head_local.xyz)
            parentId = None
            if bone.parent:
                parentId = bones.find(bone.parent.name)
            xpsBone = xps_types.XpsBone(id, name, co, parentId)
            xpsBones.append(xpsBone)

    return xpsBones

def exportMeshes(meshes):
    xpsMeshes = []
    for mesh in meshes[::-1]:
        print('Exporting Mesh:', mesh.name)
        meshName = mesh.name
        meshTextures = getXpsTextures(mesh)
        meshVertices = getXpsVertices(mesh)
        meshFaces = getXpsFaces(mesh)
        meshUvCount = len(mesh.data.uv_layers)

        xpsMesh = xps_types.XpsMesh(meshName, meshTextures, meshVertices, meshFaces, meshUvCount)
        xpsMeshes.append(xpsMesh)
    return xpsMeshes

def getXpsTextures(mesh):
    xpsTextures = []
    if mesh.material_slots:
        material = mesh.material_slots[0].material
        for textureSlot in material.texture_slots:
            if textureSlot and textureSlot.texture.type == 'IMAGE':
                xpsTexture = makeXpsTexture(mesh, material, textureSlot)
                xpsTextures.append(xpsTexture)
    return xpsTextures

def makeXpsTexture(mesh, material, textureSlot):
    texFilePath = textureSlot.texture.image.filepath
    texturePath, textureFile = os.path.split(texFilePath)
    #texFilePath = bpy.path.abspath(texFilePath)
    #texFilePath = bpy.path.relpath(texFilePath)
    uvLayerName = textureSlot.uv_layer
    uvLayerIdx = mesh.data.uv_layers.find(uvLayerName)
    id = material.texture_slots.find(textureSlot.name)

    xpsTexture = xps_types.XpsTexture(id, textureFile, uvLayerIdx)
    return xpsTexture

def getXpsVertices(mesh):
    xpsVertices = []
    uvIndexs = makeSimpleUvVert(mesh)
    vColors = makeSimpleVertColor(mesh)
    armature = getMeshArmature(mesh)
    objectMatrix = mesh.matrix_local
    for vertice in mesh.data.vertices:
        id = vertice.index
        co = coordTransform(objectMatrix * vertice.co)
        norm = coordTransform(vertice.normal)
        vColor = getVertexColor(mesh, vertice, vColors)
        uv = getUvs(mesh, vertice, uvIndexs)
        boneId = getBonesId(mesh, vertice, armature)
        boneWeight = getBonesWeight(vertice)

        xpsVertex = xps_types.XpsVertex(id, co, norm, vColor, uv, boneId, boneWeight)
        xpsVertices.append(xpsVertex)
    return xpsVertices

def makeSimpleUvVert(mesh):
    simpleUvIndex = [None] * len(mesh.data.vertices)
    for uvVert in mesh.data.loops:
        simpleUvIndex[uvVert.vertex_index] = uvVert.index
    return simpleUvIndex

def makeSimpleVertColor(mesh):
    simpleVertColors = [(255,255,255,0)] * len(mesh.data.vertices)
    vColors = None
    if mesh.data.vertex_colors:
        vColors = mesh.data.vertex_colors[0]
    if vColors:
        for uvVert in mesh.data.loops:
            color = vColors.data[uvVert.index].color
            r = rangeFloatToByte(color.r)
            g = rangeFloatToByte(color.g)
            b = rangeFloatToByte(color.b)
            a = 0
            simpleVertColors[uvVert.vertex_index] = (r, g, b, a)
    return simpleVertColors

def getMeshArmatures(mesh):
    return [modif.object for modif in mesh.modifiers if modif.type=="ARMATURE"]

def getMeshArmature(mesh):
    armatures = getMeshArmatures(mesh)
    return (armatures or [None])[0]

def getUvs(mesh, vertice, uvIndexs):
    uvs = []
    meshUvCount = len(mesh.data.uv_layers)
    for uvIdx in range(meshUvCount):
        uvCoord = mesh.data.uv_layers[uvIdx].data[uvIndexs[vertice.index]].uv
        uvCoord = uvTransform(uvCoord)
        uvs.append(uvCoord)
    return uvs

def getVertexColor(mesh, vertice, vcIndexs):
    return vcIndexs[vertice.index]

def getBonesId(mesh, vertice, armature):
    boneId = []
    for vertGroup in vertice.groups:
        #Vertex Group
        groupIdx = vertGroup.group
        boneName = mesh.vertex_groups[groupIdx].name
        boneIdx = armature.data.bones.find(boneName)
        boneId.append(boneIdx)
    boneId = fillArray(boneId, 4, 0)
    return boneId

def getBonesWeight(vertice):
    boneWeight = []
    for vertGroup in vertice.groups:
        boneWeight.append(vertGroup.weight)
    boneWeight = fillArray(boneWeight, 4, 0)
    return boneWeight

def getXpsFaces(mesh):
    mesh.data.update(calc_edges=True,calc_tessface=True)
    faces = []

    faceCount = 0
    for face in mesh.data.tessfaces:
        if len(face.vertices) == 3:
            faces.append(faceTransform(face.vertices))
            faceCount += 1
        else:
            ###TODO ngon
            verts_in_face = face.vertices
            v1, v2, v3, v4 = verts_in_face
            faces.append(faceTransform((v1, v2, v3)))
            faces.append(faceTransform((v1, v3, v4)))
            faceCount += 2

    return faces

if __name__ == "__main__":

    #filename0 = r'G:\3DModeling\XNALara\XNALara_XPS\data\TESTING5\Drake\RECB DRAKE Pack_By DamianHandy\DRAKE Sneaking Suit - Open_by DamianHandy\Generic_Item - BLENDER.mesh'
    filename1 = r'G:\3DModeling\XNALara\XNALara_XPS\data\TESTING5\Drake\RECB DRAKE Pack_By DamianHandy\DRAKE Sneaking Suit - Open_by DamianHandy\Generic_Item - BLENDER pose.mesh'

    getOutputFilename(filename1, 0, 0, True, True)

