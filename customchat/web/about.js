fetch('/api/theme').then(r=>r.json()).then(r=>{const motion=(r.theme||r).motion;document.documentElement.dataset.motion=motion;if(!['calm','none'].includes(motion)&&!matchMedia('(prefers-reduced-motion:reduce)').matches)document.querySelectorAll('.features>div,article').forEach((e,i)=>e.animate([{opacity:0,transform:'translateY(12px)'},{opacity:1,transform:'none'}],{duration:300,delay:i*50,fill:'backwards'}))}).catch(()=>{});

document.querySelectorAll('.feature-scene .draw').forEach(path=>{if(path.getTotalLength)path.style.setProperty('--length',path.getTotalLength())});
const featureObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');featureObserver.unobserve(entry.target)}}),{threshold:.2});
document.querySelectorAll('.feature-card').forEach(card=>featureObserver.observe(card));
