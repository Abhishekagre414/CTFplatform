function startLab(){
  document.getElementById("readyPanel").classList.add("hidden");
  document.getElementById("labPanel").classList.remove("hidden");
  document.getElementById("terminalPanel").classList.add("hidden");
  const frame=document.getElementById("labFrame");
  if(!frame.src) frame.src="/lab";
  document.getElementById("statusText").textContent="IN PROGRESS";
}
document.getElementById("startBtn").onclick=startLab;
document.getElementById("readyStart").onclick=startLab;
document.getElementById("browserBtn").onclick=startLab;

document.getElementById("terminalBtn").onclick=()=>{
  document.getElementById("readyPanel").classList.add("hidden");
  document.getElementById("labPanel").classList.add("hidden");
  document.getElementById("terminalPanel").classList.remove("hidden");
};

function toggleMission(id){
  document.getElementById("mission-"+id).classList.toggle("open");
}

function answerMission(id,button){
  const feedback=document.getElementById("feedback-"+id);
  fetch("/api/mission/"+id,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({answer:button.dataset.answer})
  }).then(r=>r.json()).then(data=>{
    if(data.ok){
      document.getElementById("check-"+id).textContent="✓";
      feedback.className="feedback success";
      feedback.textContent=data.all_done?"✓ Mission complete. Investigation complete!":"✓ Mission complete. Continue to the next mission.";
      document.querySelectorAll("#mission-"+id+" .option").forEach(b=>b.disabled=true);
      if(data.all_done) showFlag(data.flag);
    }else{
      feedback.className="feedback error";
      feedback.innerHTML="✗ "+data.message+"<br><small>Hint: "+data.hint+"</small>";
    }
  });
}

function showFlag(flag){
  if(document.getElementById("flagCard")) return;
  const card=document.createElement("div");
  card.id="flagCard";
  card.className="flag-card";
  card.innerHTML='<div class="flag-label">LAB COMPLETE</div><h2>🏁 Investigation Complete</h2><p>Sarah reviewed Alex’s findings. The employees now know how to spot the next suspicious email.</p><div class="flag">'+flag+"</div>";
  document.querySelector(".missions").appendChild(card);
}
