


let gCarMap = null;
const gCars = {};
let gAnimationTimer = null;


const gIcons = {};
const busIconWithColor = (color)=> L.icon({
        iconUrl: 'bus-small-'+color+'.png',
        // shadowUrl: 'leaf-shadow.png',
        iconSize:     [20, 20], // size of the icon
        // shadowSize:   [50, 64], // size of the shadow
        iconAnchor:   [10, 18], // point of the icon which will correspond to marker's location
        // shadowAnchor: [4, 62],  // the same for the shadow
        popupAnchor:  [0, -18] // point from which the popup should open relative to the iconAnchor
    });

gIcons["高速バス木更津・品川線"] = busIconWithColor('red');
gIcons["高速バス木更津・東京線"] = busIconWithColor('yellow');
gIcons["高速バス木更津・新宿線"] = busIconWithColor('blue');
gIcons["高速バス木更津・川崎線"] = busIconWithColor('skyblue');
gIcons["高速バス木更津・羽田空港線"] = busIconWithColor('green');

const gDefaultIcon = busIconWithColor('purple');


function dig02(dig){
    const d = parseInt(dig);
    return (dig < 10 ? '0':'') + d;
}

function timeSecondsToTimeStr(ts) {
    ts = parseInt(ts);
    const sec = ts % 60;
    const min = Math.floor(ts / 60) % 60;
    const hours = Math.floor(ts / 3600);
    return "" + hours + ":" + dig02(min);
}


function getStationPos(stationName){
    for(let sta of DB.stations){
        if(sta.name === stationName) {
            return sta;
        }
    }
    console.error("Invalid Station:", stationName);
    return null;
}

function interpolation(a, b, p){
    return (b - a)*p + a;
}

function interpolation2(a, b, p){
    return [
        interpolation(a[0], b[0], p),
        interpolation(a[1], b[1], p)
    ];
}


g_last_ts = null;
function updateCarsWithTime(ts) {
    ts = parseInt(ts);

    const canSkip = (g_last_ts !== null && g_last_ts <= ts);
    for(let carData of DB.cars){
        const carMarker = gCars[carData.name];
        let lastEvt = null;
        let nextEvt = null;
        let i = canSkip && carMarker.lastEventIndex ? Math.max(carMarker.lastEventIndex-1, 0) : 0;
        for(; i < carData.events.length; i++){
            const evt = carData.events[i];
            if(evt.time > ts){
                nextEvt = evt;
                break;
            }
            lastEvt = evt;
        }
        carMarker.lastEventIndex = i;

        if(lastEvt === null || nextEvt === null){
            if(carMarker.marker !== null){
                gCarMap.removeLayer(carMarker.marker);
                carMarker.marker = null;
            }
            continue;
        }
        const p = (ts - lastEvt.time)/(nextEvt.time - lastEvt.time);
        const curPos = interpolation2(lastEvt.pos, nextEvt.pos, p);
        if(carMarker.marker === null){
            let carIcon = gDefaultIcon;
            if(carData.line in gIcons){
                carIcon = gIcons[carData.line];
            }
            carMarker.marker = L.marker(curPos, {
                icon: carIcon,
                title: "タイトル:" + carData.name
            });
            carMarker.marker.bindPopup(""+carData.name);
            carMarker.marker.addTo(gCarMap);
        }else{
            carMarker.marker.setLatLng(curPos);
        }
    }

}

function stopAnimationTimer(){
    if(gAnimationTimer !== null) {
        clearInterval(gAnimationTimer);
        gAnimationTimer = null;
    }
}

function increseTime(tv){
    const newVal = parseInt($('.timeslider').val()) + tv;
    $('.timeslider').val(newVal);
    $('.timeval').text("TIME: " + timeSecondsToTimeStr(newVal) + " (Animating)");
    updateCarsWithTime(newVal);
}



function main(){

    gCarMap = L.map('mapbox').setView([35.38143, 139.92711], 12);
    for(let car of DB.cars) {
        gCars[car.name] = {
            marker: null,
            lastEventIndex: -1
        };
    }

    L.tileLayer(
        'https://tile.openstreetmap.jp/{z}/{x}/{y}.png',
        {
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
            maxZoom: 18
        }
    ).addTo(gCarMap);






    $('.timeslider').on('change', ()=>{
        const tv = $('.timeslider').val();
        $('.timeval').text("TIME: " + timeSecondsToTimeStr(tv));
        updateCarsWithTime(tv);
        // const pos = new L.LatLng(36.3219088 + parseFloat(tv) * 0.00001, 139.0032936);
        // marker.setLatLng(pos);
    });

    $('.play1_btn').on('click', ()=>{
        stopAnimationTimer();
        gAnimationTimer = setInterval(()=>{
            increseTime(1);
        }, 10);
    });

    $('.play_with_speed_btn').on('click', (e)=>{
        stopAnimationTimer();
        const speed = $(e.currentTarget).attr('speed');
        const timerInterval = $(e.currentTarget).attr('interval');

        gAnimationTimer = setInterval(()=>{
            increseTime(parseInt(speed));
        }, timerInterval);
    });

    $('.play10_btn').on('click', ()=>{
        stopAnimationTimer();
        gAnimationTimer = setInterval(()=>{
            increseTime(10);
        }, 10);
    });

    $('.stop_btn').on('click', ()=>{
        stopAnimationTimer();
    });


    // Route Builder
    let gRouteMarkers = [];
    gCarMap.on('contextmenu',function(e){
        const $line = $('<div class="point"></div>');
        $line.text('   - [' + e.latlng.lat + ', ' + e.latlng.lng + ']');
        $('.route-data').append($line);
        const marker = L.marker(e.latlng).addTo(gCarMap);
        gRouteMarkers.push(marker);
    });

    $('.route-remove-one-button').on('click', ()=>{
        if(gRouteMarkers.length == 0){
            return;
        }
        gCarMap.removeLayer(gRouteMarkers.pop());
        $('.route-data .point:last').remove();

    });

    $('.route-clear-button').on('click', ()=>{
        for(let marker of gRouteMarkers){
            gCarMap.removeLayer(marker);
        }
        gRouteMarkers = [];
        $('.route-data .point').remove();
    });

}





$(main);
