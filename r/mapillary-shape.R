#
# file:     mapillary-shape.R
#
# coder:    moenkemt@geo.hu-berlin.de
#
# purpose:  download picture urls in bounding box and save as shapefile
#           also writes an openlayers textfile for simple web review
#

# my working directory
setwd("~/public_html/mapillary")

# libs
library(sp);
library(rgdal);
library(raster);
library(RCurl);
library(jsonlite);

# bounding box for pictures
minlon=13.345921;
minlat=52.493017;
maxlon=13.363731;
maxlat=52.503885;

client_id="***";

page=0;
 repeat {
    url=paste("https://a.mapillary.com/v2/search/im?client_id=",client_id,
            "&min_lon=",minlon,
            "&min_lat=",minlat,
            "&max_lon=",maxlon,
            "&max_lat=",maxlat,
            "&page=",page,
            sep="")

  json_doc=getURL(url);
  data=fromJSON(json_doc);
  if (page==0) {
    shapedata=data$ims;
  } else {
    shapedata=rbind(shapedata,data$ims);
  }
  page=page+1;
  if (data$more==FALSE) break;
}

# converte fields
shapedata$timestamp=as.POSIXct(shapedata$captured_at/1000,origin="1970-01-01");
shapedata$image=paste("https://d1cuyjsrcm0gby.cloudfront.net",shapedata$key,"thumb-1024.jpg",sep="/");

# create shapefile
shapefile=SpatialPointsDataFrame(shapedata[4:5],shapedata);
projection(shapefile)=CRS("+proj=longlat +datum=WGS84");
writeOGR(shapefile, dsn = '.', layer ='mapillary', driver = 'ESRI Shapefile', overwrite=TRUE);
plot(shapefile);

# save openlayers textfile
shapedata$title=shapedata$location;
shapedata$title[shapedata$title==""]="*";
shapedata$description=paste("<a target='_blank' href='",shapedata$image,"'><img src='https://d1cuyjsrcm0gby.cloudfront.net/",
                                        shapedata$key,"/thumb-320.jpg'></a>",
                                        sep="");
write.table(shapedata[,c("lon","lat","title","description")],
            file= "mapillary.txt",
            sep="\t",
            row.names=FALSE,
            quote=FALSE);

#system("zip mapillary.zip mapillary.*");

