<?php
//
//	file: my_mapillary.php
//
//	coder: moenkemt@geo.hu-berlin.de
//
//	purpose: display my latest sequences uploaded to mapillary for embedding in my blog
//

//
// config
//
$client_id="***";
$my_username="moenk";
$osm_zoom=16;

//
// main
//
$url="https://a.mapillary.com/v2/search/s?client_id=".$client_id."&limit=12&&user=".$my_username;
$json=file_get_contents($url);
$data = json_decode($json);
// print "<pre>"; print_r($data); die();
foreach ($data->ss as $sequence) {
    $images=$sequence->keys;
	$capture=date("Y-m-d H:i",intval($sequence->captured_at/1000));
	$coords=$sequence->coords;
	$lon=floatval($coords[0][0]);
	$lat=floatval($coords[0][1]);
    $xtile = floor((($lon + 180) / 360) * pow(2, $osm_zoom));
    $ytile = floor((1 - log(tan(deg2rad($lat)) + 1 / cos(deg2rad($lat))) / pi()) /2 * pow(2, $osm_zoom));
	print "<p>";
	print "<a rel='nofollow' target='_new' href='https://www.mapillary.com/map/im/".$images[0]."/photo'>\n";
	print "<img style='border:5px solid white; width:240px; height=180px;' src='https://d1cuyjsrcm0gby.cloudfront.net/".$images[0]."/thumb-320.jpg'>\n";
	print "</a>\n";
	print "<a rel='nofollow' target='_new' href='https://www.mapillary.com/map/im/".$images[0]."/map'>\n";
    $tileurl="<img style='border:5px solid white; width:180px; height=180px' src=\"http://tile.openstreetmap.org/".$osm_zoom."/".$xtile."/".$ytile.".png\">";
	print $tileurl."</a>";
	print "<br />".$capture." &bull; ".count($images)." images in sequence.";
	print "</p>\n";
}
?>