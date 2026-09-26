(function(){
  async function setupCamera(videoId,canvasId,buttonId,statusId,key){
    const video=document.getElementById(videoId),canvas=document.getElementById(canvasId),button=document.getElementById(buttonId),status=document.getElementById(statusId);
    if(!video||!canvas||!button)return;
    if(!navigator.mediaDevices?.getUserMedia){status.textContent='Your browser does not provide camera access here.';return;}
    let stream;
    try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;status.textContent='Camera ready.';}
    catch(e){status.textContent='Camera access is required for a live photo.';return;}
    button.addEventListener('click',()=>{
      canvas.width=video.videoWidth||640;canvas.height=video.videoHeight||480;canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
      const data=canvas.toDataURL('image/jpeg',0.85);sessionStorage.setItem(key+'_captured','true');sessionStorage.setItem(key+'_data',data);status.textContent='Live photo captured. Your profile photo is now ready.'; status.classList.add('success'); button.disabled=true; window.dispatchEvent(new Event('continuum-photo-captured'));
    });
    window.addEventListener('beforeunload',()=>stream?.getTracks().forEach(t=>t.stop()));
  }
  setupCamera('livePhoto','livePhotoCanvas','takeLivePhoto','livePhotoStatus','continuum_live_photo');
  setupCamera('recoveryLivePhoto','recoveryPhotoCanvas','takeRecoveryPhoto','recoveryPhotoStatus','continuum_recovery_photo');
})();
