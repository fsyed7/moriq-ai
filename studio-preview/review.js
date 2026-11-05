const frame=document.querySelector('iframe');
const stage=document.querySelector('.stage');
function size(){
 const width=location.hash==='#desktop'?1280:location.hash==='#tablet'?768:390;
 const scale=Math.min(1,(stage.clientWidth-32)/width);
 frame.style.width=width+'px';frame.style.height='940px';frame.style.transform='scale('+scale+')';
 frame.style.marginLeft=Math.max(0,(stage.clientWidth-32-width*scale)/2)+'px';
 stage.style.height=(940*scale+24)+'px';
 document.querySelector('#size-label').textContent=width+'px layout · '+Math.round(scale*100)+'% display scale · DEMO / FIXTURE DATA';
}
addEventListener('hashchange',size);new ResizeObserver(size).observe(stage);size();
new EventSource('/events').onmessage=event=>{if(JSON.parse(event.data).some(f=>f==='review.html'||f==='review.js'))location.reload();};
