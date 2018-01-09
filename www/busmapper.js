


let gCarMap = null;
const gCars = {};
let gAnimationTimer = null;

function timeSecondsToTimeStr(ts) {
    ts = parseInt(ts);
    const sec = ts % 60;
    const min = Math.floor(ts / 60) % 60;
    const hours = Math.floor(ts / 3600);
    return "" + hours + ":" + min;
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

function updateCarsWithTime(ts) {
    ts = parseInt(ts);

    for(let carData of DB.cars){
        const carMarker = gCars[carData.name];
        let lastEvt = null;
        let nextEvt = null;
        for(let evt of carData.events){
            if(evt.time > ts){
                nextEvt = evt;
                break;
            }
            lastEvt = evt;
        }
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
            carMarker.marker = L.marker(curPos).addTo(gCarMap);
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
            marker: null
        };
    }

    L.tileLayer(
        'https://tile.openstreetmap.jp/{z}/{x}/{y}.png',
        {
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
            maxZoom: 18
        }
    ).addTo(gCarMap);


    const marker = L.marker([36.3219088, 139.0032936]).addTo(gCarMap);

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

    $('.play10_btn').on('click', ()=>{
        stopAnimationTimer();
        gAnimationTimer = setInterval(()=>{
            increseTime(10);
        }, 10);
    });

    $('.stop_btn').on('click', ()=>{
        stopAnimationTimer();
    });
}





$(main);
