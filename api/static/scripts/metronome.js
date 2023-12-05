let intervalId;
let audioContext;
let isMetronomePlaying = false;

function updateTempoValue() {
  const tempoInput = document.getElementById("tempo");
  const tempoValueSpan = document.getElementById("tempo_value");
  const tempo = tempoInput.value;
  tempoValueSpan.textContent = tempo;

  // If the metronome is playing, update the tempo dynamically
  if (isMetronomePlaying) {
    stopMetronome();
    startMetronome();
  }
}

function toggleMetronome() {
  if (isMetronomePlaying) {
    stopMetronome();
    document.getElementById("metronome-button").textContent = "⏵";
  } else {
    startMetronome();
    document.getElementById("metronome-button").textContent = "⏸";
  }

  // Toggle the state
  isMetronomePlaying = !isMetronomePlaying;
}

function startMetronome() {
  const tempoInput = document.getElementById("tempo");
  var tempo = parseInt(tempoInput.value, 10);

  // Create or recreate the audio context
  
  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  var count = 0;

  intervalId = setInterval(() => {
    // Check if audio context is available
    if (!audioContext) {
      stopMetronome();
      startMetronome();
    }

    tickSound = audioContext.createBufferSource();

    const tickSoundUrl = document.getElementById("tickSound").dataset.url;

    fetch(tickSoundUrl)
      .then(response => response.arrayBuffer())
      .then(buffer => audioContext.decodeAudioData(buffer))
      .then(audioBuffer => {
        tickSound.buffer = audioBuffer;
        tickSound.connect(audioContext.destination);
        tickSound.start();
      })
      .catch(error => console.error('Error loading audio file:', error));

  }, (60 / tempo) * 1000); // Convert tempo to milliseconds
}

function stopMetronome() {
  if (intervalId) {
    clearInterval(intervalId);
  }
  if (audioContext && audioContext.state !== 'closed') {
    // Check if the AudioContext is not closed
    audioContext.close().then(() => {
      audioContext = null;
    });
  }
}