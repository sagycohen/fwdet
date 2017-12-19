'''
InundationDepth_Focal.py

Floodwater Depth Estimation Tool (FwDET)

Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM.
Program procedure:
1. Flood extent polygon to polyline
2. Polyline to Raster - DEM extent and resolution (Env)
3. Con - DEM values to Raster
4. Focal Statistics loop
5. Water depth calculation - difference between Focal Statistics output and DEM 

See:
Cohen, S., G. R. Brakenridge, A. Kettner, B. Bates, J. Nelson, R. McDonald, Y. Huang, D. Munasinghe, and J. Zhang (2017), 
	Estimating Floodwater Depths from Flood Inundation Maps and Topography. Journal of the American Water Resources Association (JAWRA):1–12.

Created by Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
email: sagy.cohen@ua.edu
web: http://sdml.ua.edu
June 30, 2016

Copyright (C) 2017 Sagy Cohen
Developer can be contacted by sagy.cohen@ua.edu and Box 870322, Tuscaloosa AL 35487 USA
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import arcpy
from arcpy.sa import *

def main():
    arcpy.CheckOutExtension("Spatial") #require an ArcGIS Spatial Analyst extension
    arcpy.env.overwriteOutput = True
    WS = arcpy.env.workspace = r'Lyons.gdb' #location of workspace (preferably a Geodatabase)
    arcpy.env.scratchWorkspace = r'Scratch.gdb' #location of the Scratch Geodatabase (optional but highly recommended)
    DEMname = 'Elevation'  #name of the input DEM (within the Workspace)
    InundPolygon = 'FloodExtent' #name of the input Inundation extent polygon layer (within the Workspace)
    ClipDEM = 'dem_clip' #name of the output clipped DEM (clipped by the inundation polygon extent)

    dem = arcpy.Raster(DEMname)
    cellSize = dem.meanCellHeight
    boundary = CalculateBoundary(dem, InundPolygon, cellSize, WS)
   # boundary = Raster('boundary1') # a raster layer with only the boundary cells having value (elevation) - generated by the CalculateBoundary function - an existing one can be entered here 
    extent = str(dem.extent.XMin) + " " + str(dem.extent.YMin) + " " + str(dem.extent.XMax) + " " + str(dem.extent.YMax)
    print extent
    
    arcpy.Clip_management(DEMname, extent, ClipDEM, InundPolygon, cellSize, 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
    #ClipDEM = arcpy.Raster(ClipDEM) # The DEM is clipped - using the Clip_management tool - an existing one can be entered here  
    print arcpy.GetMessages()
    arcpy.env.extent = arcpy.Extent(dem.extent.XMin,dem.extent.YMin,dem.extent.XMax,dem.extent.YMax)

    print 'First focal '
    OutRas = FocalStatistics(boundary, 'Circle 3 CELL', "MAXIMUM", "DATA")
    
# the Focal Statistics loop - Number of iteration will depend on the flood inundation extent and DEM resolution - Change here!!!!
    for i in range(3, 50):         print i
        negihbor = 'Circle ' + str(i) + ' CELL'
        # negihbor = 'Rectangle ' + str(i) + ' ' + str(i) + ' CELL'
        OutRasTemp = FocalStatistics(boundary, negihbor, "MAXIMUM", "DATA")
        OutRas = Con(IsNull(OutRas), OutRasTemp, OutRas) #assure that only 'empty' (NoDATA) cells are assigned a value in each iteration
    print 'Focal loop done!'
   
    OutRas.save('Focafin10m') #name of output final focal statistics raster
   
    waterDepth = Minus(OutRas, ClipDEM) #Calculate floodwater depth 
    waterDepth = Con(waterDepth < 0, 0, waterDepth)
    waterDepth.save('WaterDepth10m') #name of output floodwater depth raster
    waterDepthFilter = Filter(waterDepth, "LOW", "DATA")
    waterDepthFilter.save('WaterDep10mf') #name of output floodwater depth raster after low-pass filter 

    print 'Done'

def CalculateBoundary(dem, InundPolygon,cellSize,WS):
    arcpy.PolygonToLine_management(InundPolygon, WS+'\polyline') #Convert inundation extent polygon to polyline
    arcpy.PolylineToRaster_conversion(WS+'\\polyline', 'OBJECTID', WS+'\linerast15', 'MAXIMUM_LENGTH', 'NONE', cellSize) #Convert polyline to raster
    print 'after polyline to raster'
    inRaster = Raster(WS+'\linerast15')
    inTrueRaster = dem
    inFalseConstant = '#'
    whereClause = "VALUE >= 0"
    print 'Con'
    boundary = Con(inRaster, inTrueRaster, inFalseConstant, whereClause) #extract the boundary cells elevation from a DEM
    boundary.save('boundary1') #name of output boundary cell elevation raster
    return boundary
main()
