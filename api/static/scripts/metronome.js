let audioContext;
let tickBuffer;
let tickSource;
let isMetronomePlaying = false;
let baseVolume = 1; // Adjust this value to control the base volume

function updateTempoValue() {
  const tempoInput = document.getElementById("tempo");
  const tempoValueSpan = document.getElementById("tempo_value");
  const tempo = parseInt(tempoInput.value, 10);
  tempoValueSpan.textContent = tempo;

  if (isMetronomePlaying) {
    updatePlaybackRate(tempo);
    updateVolume(tempo);
  }
}

function toggleMetronome() {
  if (isMetronomePlaying) {
    stopMetronome();
    document.getElementById("metronome-button").textContent = "⏵";
  } else {
    const tempoInput = document.getElementById("tempo");
    const tempo = parseInt(tempoInput.value, 10);
    startMetronome(tempo);
    document.getElementById("metronome-button").textContent = "⏸";
  }

  // Toggle the state
  isMetronomePlaying = !isMetronomePlaying;
}

function loadAudio() {
  const tickSoundUrl = document.getElementById("tickSound").dataset.url;

  return fetch(tickSoundUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.arrayBuffer();
    })
    .then(buffer => audioContext.decodeAudioData(buffer));
}

function createTickSource() {
  tickSource = audioContext.createBufferSource();
  tickSource.buffer = tickBuffer;
  
  // Create a gain node and connect it to the audio context
  tickSource.gainNode = audioContext.createGain();
  tickSource.connect(tickSource.gainNode);
  tickSource.gainNode.connect(audioContext.destination);
  
  tickSource.loop = true;
}

function startMetronome(tempo) {
  stopMetronome(); // Stop any existing metronome

  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  } catch (error) {
    console.error("Error creating AudioContext:", error);
    return;
  }

  if (!audioContext) {
    stopMetronome();
    startMetronome(tempo);
    return;
  }

  loadAudio()
    .then(audioBuffer => {
      tickBuffer = audioBuffer;
      createTickSource();
      updatePlaybackRate(tempo);
      updateVolume(tempo);
      tickSource.start();
    })
    .catch(error => console.error('Error loading audio file:', error));
}

function updatePlaybackRate(tempo) {
  tickSource.playbackRate.value = calculatePlaybackRate(tempo);
}

function updateVolume(tempo) {
  // Adjust volume based on the tempo
  const maxTempo = 200; // Adjust this value if needed
  const volumeAdjustment = baseVolume * (1 - Math.min(tempo, maxTempo) / maxTempo);
  tickSource.gainNode.gain.value = baseVolume - volumeAdjustment;
}

function calculatePlaybackRate(tempo) {
  const baseTempo = 60;
  return tempo / baseTempo;
}

function stopMetronome() {
  if (tickSource) {
    tickSource.stop();
    tickSource.disconnect();
    tickSource = null;
  }

  if (audioContext && audioContext.state !== 'closed') {
    // Check if the AudioContext is not closed
    audioContext.close().then(() => {
      audioContext = null;
    });
  }
}