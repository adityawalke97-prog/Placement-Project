document.addEventListener('DOMContentLoaded', () => {
  const course = document.getElementById('courseSelect');
  const subject = document.getElementById('subjectSelect');
  if (course && subject) {
    course.addEventListener('change', async () => {
      subject.innerHTML = '<option value="">Loading subjects...</option>';
      if (!course.value) { subject.innerHTML = '<option value="">First select course</option>'; return; }
      try {
        const response = await fetch(`/mock-tests/api/subjects/${course.value}`);
        const data = await response.json();
        subject.innerHTML = '<option value="">Select subject</option>';
        data.subjects.forEach(s => { const option = document.createElement('option'); option.value=s.id; option.textContent=s.subject_name; subject.appendChild(option); });
      } catch { subject.innerHTML = '<option value="">Could not load subjects</option>'; }
    });
  }
  document.querySelectorAll('[data-copy]').forEach(btn => btn.addEventListener('click', async () => {
    const input = document.getElementById(btn.dataset.copy); input.select(); await navigator.clipboard.writeText(input.value); btn.textContent='Copied!';
  }));
  document.querySelectorAll('[data-copy-text]').forEach(btn => btn.addEventListener('click', async () => {
    await navigator.clipboard.writeText(btn.dataset.copyText); btn.textContent='Copied!';
  }));

  const form = document.getElementById('attemptForm');
  if (!form) return;
  const sections = [...document.querySelectorAll('.mt-question')];
  const palette = [...document.querySelectorAll('.palette-btn')];
  const answeredCount = document.getElementById('answeredCount');
  let current = 0;
  const storageKey = `mock-test-${form.action.split('/').pop()}`;
  function update() {
    const answered = form.querySelectorAll('input[type=radio]:checked').length;
    answeredCount.textContent = `${answered} / ${sections.length} answered`;
    palette.forEach((button,i) => {
      button.classList.toggle('active', i===current);
      button.classList.toggle('answered', !!sections[i].querySelector('input:checked'));
    });
  }
  function show(index) { current=Math.max(0,Math.min(index,sections.length-1)); sections.forEach((s,i)=>s.classList.toggle('hidden',i!==current)); update(); }
  palette.forEach((b,i)=>b.addEventListener('click',()=>show(i)));
  document.getElementById('prevQuestion').addEventListener('click',()=>show(current-1));
  document.getElementById('nextQuestion').addEventListener('click',()=>show(current+1));
  form.addEventListener('change', () => { update(); saveAnswers(); });
  function saveAnswers(){ const answers={}; form.querySelectorAll('input:checked').forEach(x=>answers[x.name]=x.value); try{localStorage.setItem(storageKey,JSON.stringify(answers));}catch{} }
  try { const saved=JSON.parse(localStorage.getItem(storageKey)||'{}'); Object.entries(saved).forEach(([name,value])=>{const radio=form.querySelector(`input[name="${CSS.escape(name)}"][value="${value}"]`);if(radio)radio.checked=true;}); } catch {}
  update();
  const modal=document.getElementById('submitModal');
  document.getElementById('openSubmit').addEventListener('click',()=>{const done=form.querySelectorAll('input:checked').length;document.getElementById('submitSummary').textContent=`You answered ${done} out of ${sections.length}. Unanswered questions will be marked incorrect.`;modal.classList.remove('hidden');});
  document.getElementById('cancelSubmit').addEventListener('click',()=>modal.classList.add('hidden'));
  document.getElementById('confirmSubmit').addEventListener('click',()=>{localStorage.removeItem(storageKey);form.submit();});
  const timer=document.getElementById('timer'); let seconds=Number(timer.dataset.seconds||0);
  function tick(){const m=Math.floor(seconds/60),s=seconds%60;timer.textContent=`${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;if(seconds<=0){localStorage.removeItem(storageKey);form.submit();return;}seconds--;}
  tick(); const interval=setInterval(()=>{if(!document.body.contains(timer)){clearInterval(interval);return;}tick();},1000);
  document.addEventListener('keydown',e=>{if(e.key==='ArrowRight')show(current+1);if(e.key==='ArrowLeft')show(current-1);});
});
