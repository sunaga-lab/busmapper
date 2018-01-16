


ENABLE_EVENT_SIGNS = false;
ENABLE_SOUNDS = false;


let gCarMap = null;
const gCars = {};
let gAnimationTimer = null;


const gIcons = {};
const busIconWithColor = (color)=> L.icon({
        iconUrl: 'icons/bus-icon-'+color+'.png',
        // shadowUrl: 'leaf-shadow.png',
        iconSize:     [26, 26], // size of the icon
        // shadowSize:   [50, 64], // size of the shadow
        iconAnchor:   [13, 20], // point of the icon which will correspond to marker's location
        // shadowAnchor: [4, 62],  // the same for the shadow
        popupAnchor:  [0, -20] // point from which the popup should open relative to the iconAnchor
    });

gIcons["高速バス木更津・品川線"] = busIconWithColor('red');
gIcons["高速バス木更津・東京線"] = busIconWithColor('purple');
gIcons["高速バス木更津・新宿線"] = busIconWithColor('blue');
gIcons["高速バス木更津・川崎線"] = busIconWithColor('cyan');
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



const g_sound_map = [
    ['tone-sin-E2-fo', 'tick2min'],
    ['tone-sin-A4-fo', '高速バス木更津・羽田空港線', '下り'],
    ['tone-sin-E5-fo', '高速バス木更津・東京線', '下り'],
    ['tone-sin-C5-fo', '高速バス木更津・新宿線', '下り'],
    ['tone-sin-A6-fo', '高速バス木更津・品川線', '下り'],
    ['tone-sin-A5-fo', '高速バス木更津・川崎線', '下り'],

    ['tone-sin-A3-fo', '高速バス木更津・羽田空港線', '上り'],
    ['tone-sin-E4-fo', '高速バス木更津・東京線', '上り'],
    ['tone-sin-C4-fo', '高速バス木更津・新宿線', '上り'],
    ['tone-sin-E3-fo', '高速バス木更津・品川線', '上り'],
    ['tone-sin-C3-fo', '高速バス木更津・川崎線', '上り'],
]

const g_audio_objs = {};

function prepare_audio() {
    for(let line of g_sound_map){
        const fn = line[0];
        if(fn in g_audio_objs){
            continue;
        }
        g_audio_objs[fn] = [];
        for(let i = 0; i < 8; i++){
            const audio = new Audio('sounds/' + fn + '.mp3');
            audio.volume = 0.05;
            g_audio_objs[fn].push(audio);
        }
    }
}

function play_sound_for(key) {
    for(let line of g_sound_map){
        let matchAutio = line[0];
        for(let elem of line.slice(1)){
            if(key.indexOf(elem) == -1){
                matchAutio = null;
                break;
            }
        }
        if(matchAutio !== null){
            for(let audio of g_audio_objs[matchAutio]){

                if(audio.paused){
                    audio.play();
                    return;
                }
            }
            console.warn("Too many play for:" + matchAutio);
            return;
        }
    }
    console.warn("Not match for:" + key);
}

g_last_ts = null;
g_last_event_mark_index = 0;

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

    // 音を鳴らす
    if(ENABLE_EVENT_SIGNS && ENABLE_SOUNDS) {
        if (canSkip) {
            const play_sounds = {};
            while (DB.event_signs.length > g_last_event_mark_index) {
                const sign = DB.event_signs[g_last_event_mark_index];
                if (sign.ts <= g_last_ts) {
                    g_last_event_mark_index += 1;
                    continue;
                }
                if (sign.ts > ts) {
                    break;
                }
                play_sounds[sign.mark] = 1;
                g_last_event_mark_index += 1;
            }

            for (let key in play_sounds) {
                play_sound_for(key);
            }
        } else {
            g_last_event_mark_index = 0;
        }
    }
    g_last_ts = ts;
}

function stopAnimationTimer(){
    if(gAnimationTimer !== null) {
        clearInterval(gAnimationTimer);
        gAnimationTimer = null;
    }
}

g_last_time = null;
function increseTime(tv){
    const now_t = new Date().getTime();
    if(!g_last_time || now_t < g_last_time){
        g_last_time = now_t;
    }

    increseStep(tv * (now_t - g_last_time) / 1000.0);
    g_last_time = now_t;
}

function increseStep(step) {
    const newVal = parseFloat($('.timeslider').val()) + (step);
    $('.timeslider').val(newVal);
    $('.timeval').text(timeSecondsToTimeStr(newVal));
    $('.otherval').text("(Animating) raw=" + newVal);
    updateCarsWithTime(newVal);

}

function main(){

    prepare_audio();

    gCarMap = L.map('mapbox', { zoomControl:false }).setView([35.52800, 139.83000], 11);
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
        $('.timeval').text(timeSecondsToTimeStr(tv));
        $('.otherval').text("");
        updateCarsWithTime(tv);
        // const pos = new L.LatLng(36.3219088 + parseFloat(tv) * 0.00001, 139.0032936);
        // marker.setLatLng(pos);
    });


    $('.play_step_btn').on('click', (e)=>{
        const step = $(e.currentTarget).attr('step');
        increseStep(parseFloat(step));

    });

    $('.play_with_speed_btn').on('click', (e)=>{
        stopAnimationTimer();
        const speed = $(e.currentTarget).attr('speed');
        const timerInterval = $(e.currentTarget).attr('interval');

        gAnimationTimer = setInterval(()=>{
            increseTime(parseFloat(speed));
        }, 1);
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

    $('.rendermode_btn').on('click', ()=>{
        $('body').addClass('render-mode')
    });

}





$(main);
