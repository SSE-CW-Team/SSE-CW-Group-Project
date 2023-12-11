var selectedWorkoutType;

var previousSelectedWorkout = null; // Global variable to remember the last selected workout

// Function to filter options based on user input
function filterOptions() {
  updateLikedSongsValue();
  var input = document.getElementById("genre").value.toLowerCase();
  var options = document.getElementById("genreList").getElementsByTagName("option");

  for (var i = 0; i < options.length; i++) {
    var optionValue = options[i].value.toLowerCase();
    if (optionValue.startsWith(input)) {
      options[i].setAttribute("data-match", "true");
    } else {
      options[i].removeAttribute("data-match");
    }
  }

  // Remove non-matching options from the list
  var nonMatchingOptions = datalist.querySelectorAll("option:not([data-match])");
  nonMatchingOptions.forEach(function (option) {
    option.remove();
  });
}

function checkStatus() {
  fetch("/check_task_status")
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "complete") {
        window.location.href = "/export";
      } else {
        setTimeout(checkStatus, 2000); // Check again after 2 seconds
      }
    });
}

document.addEventListener("DOMContentLoaded", (event) => {
  document.getElementById("generatePlaylistButton").addEventListener("click", function (event) {
    checkStatus();
  });
});

function updateLikedSongsValue() {
  var slider = document.getElementById("liked_songs");
  var valueDisplay = document.getElementById("liked_songs_value");
  var steppedValue = Math.round(slider.value / 20) * 20; // Round to the nearest multiple of 20
  valueDisplay.innerHTML = steppedValue;
}
// Function to add selected option to the list
function addToSelectedList() {
  var genres_text = document.getElementById("selectedGenresText");
  genres_text.innerHTML = "Selected genres:";
  var inputElement = document.getElementById("genre");

  // Check if the input box is empty
  if (inputElement.value.trim() === "") {
    return; // Exit early if there is no text
  }
  var selectedItem = inputElement.value.trim().toLowerCase();
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");

  // Filter dropdown options based on user input
  var filteredOptions = Array.from(dropdownOptions).filter((option) => option.value.toLowerCase() === selectedItem);

  if (filteredOptions.length === 0) {
    return; // Exit early if there are no filtered options
  }

  // Check if there are matching options in the filtered list
  var matchingOption = filteredOptions.length > 0 ? filteredOptions[0] : null;

  // If there is no match in the filtered list, use the top value from the original dropdown
  if (!matchingOption && dropdownOptions.length > 0) {
    matchingOption = dropdownOptions[0];
  }

  // Add the selected option to the list
  addOptionToSelectedList(matchingOption.value);

  // Clear the input field
  inputElement.value = "";
}

// Event listener for keydown event on the input field
document.getElementById("genre").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    // Prevent the default behavior of the Enter key
    event.preventDefault();
    addToSelectedList(); // Simulate a click on the most relevant value
  }
});

// Event listener for input changes on the genre input field
document.getElementById("genre").addEventListener("input", function (event) {
  var inputElement = event.target;
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");

  var isOption = Array.from(dropdownOptions).some((option) => option.value === inputElement.value);

  if (isOption) {
    addToSelectedList(); // Add the genre to the selected list
    inputElement.value = ""; // Clear the input field
  }
});

// Function to add the selected option to the list
function addOptionToSelectedList(selectedItem) {
  var selectedList = document.getElementById("selectedList");
  var listItem = document.createElement("li");
  listItem.textContent = selectedItem;

  // Create a remove button
  var removeButton = document.createElement("button");
  removeButton.textContent = "Remove";
  removeButton.classList.add("remove");
  var removeTextColour = "#ffffff";
  let removeColour;
  switch (selectedWorkoutType) {
    case "running":
      removeColour = "#0a3808";
      break;
    case "boxing":
      removeColour = "#412275";
      break;
    case "cycling":
      removeColour = "#080d38";
      break;
    case "yoga":
      removeColour = "#adad02";
      removeTextColour = "#000000";
      break;
    case "gym":
      removeColour = "#7a0202";
      break;
    default:
      removeColour = "#737373";
      removeTextColour = "#000000";
  }
  removeButton.style.background = removeColour;
  removeButton.style.color = removeTextColour;
  removeButton.addEventListener("click", function () {
    var removedGenre = listItem.textContent.trim();
    listItem.remove();
    updateHiddenInput(); // Update the hidden input when removing an item
    addOptionBackToDropdown(removedGenre); // Add the removed option back to the dropdown
  });

  // Append the remove button to the list item
  listItem.appendChild(removeButton);

  // Find the correct position to insert the new item in alphabetical order
  var existingItems = selectedList.getElementsByTagName("li");
  var insertIndex = 0;

  for (var i = 0; i < existingItems.length; i++) {
    var existingItemText = existingItems[i].textContent.trim();
    if (selectedItem.toLowerCase() > existingItemText.toLowerCase()) {
      insertIndex = i + 1;
    } else {
      break;
    }
  }

  // Insert the new item at the correct position
  if (insertIndex < existingItems.length) {
    selectedList.insertBefore(listItem, existingItems[insertIndex]);
  } else {
    selectedList.appendChild(listItem);
  }

  // Remove the selected genre from the dropdown list
  removeOptionFromDropdown(selectedItem);

  updateHiddenInput(); // Update the hidden input when adding an item

  printSelectedListState();
}

function toggleAdvancedOptions() {
  var advancedSearchContainer = document.getElementById("advanced-search-container");
  var advancedSearchCheckbox = document.getElementById("advanced-search-checkbox");

  // Toggle the display of the advanced search container based on the checkbox state
  advancedSearchContainer.style.display = advancedSearchCheckbox.checked ? "block" : "none";
}

// Function to print the current state of the selected list to the console
function printSelectedListState() {
  var selectedGenres = getSelectedGenres();
}

// Function to remove the selected option from the dropdown list
function removeOptionFromDropdown(optionText) {
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");
  for (var i = 0; i < dropdownOptions.length; i++) {
    if (dropdownOptions[i].value.toLowerCase() === optionText.toLowerCase()) {
      dropdownOptions[i].remove();
      break;
    }
  }
}

// Function to add the removed option back to the dropdown list at the correct alphabetical spot
function addOptionBackToDropdown(optionText) {
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");
  for (var i = 0; i < dropdownOptions.length; i++) {
    if (optionText.toLowerCase() < dropdownOptions[i].value.toLowerCase()) {
      var newOption = document.createElement("option");
      optionText = optionText.endsWith("Remove") ? optionText.slice(0, -"Remove".length) : optionText;
      newOption.value = optionText;
      dropdownOptions[i].parentNode.insertBefore(newOption, dropdownOptions[i]);
      break;
    }
  }
  // If the option should be added at the end
  if (i === dropdownOptions.length) {
    var newOption = document.createElement("option");
    optionText = optionText.endsWith("Remove") ? optionText.slice(0, -"Remove".length) : optionText;
    newOption.value = optionText;
    document.getElementById("genreList").appendChild(newOption);
  }
}

// Event listener for when an option is selected
document.getElementById("genre").addEventListener("change", addToSelectedList);

// Add an event listener for the pageshow event
window.addEventListener('pageshow', function (event) {
  // Check if the loading container was visible before navigating away
  const loadingContainer = document.getElementById("loading-container");
  
  // If it was visible, hide it
  if (loadingContainer.style.display === "block") {
    loadingContainer.style.display = "none";
    document.getElementById("generatePlaylistButton").style.display = "block";
  }
});

// Function to update the hidden input with selected genres
function updateHiddenInput() {
  var selectedGenres = getSelectedGenres();
  document.getElementById("selectedGenres").value = selectedGenres.join(", ");
}

// Function to get selected genres from the list
function getSelectedGenres() {
  var selectedGenres = [];
  var selectedOptions = document.getElementById("selectedList").getElementsByTagName("li");

  for (var i = 0; i < selectedOptions.length; i++) {
    var genreText = selectedOptions[i].innerText.trim();
    genreText = genreText.endsWith("Remove") ? genreText.slice(0, -"Remove".length) : genreText;
    selectedGenres.push(genreText);
  }

  return selectedGenres;
}

function updateDefaultValues(newWorkout) {
  previousSelectedWorkout = selectedWorkoutType;
  // Define what to do when the user confirms
  var onConfirm = function (workout) {
    // Logic to execute when the user confirms
    applyWorkoutChanges(workout);
  };

  // Define what to do when the user cancels
  var onCancel = function () {
    revertWorkoutSelection();
  };

  if (selectedWorkoutType === newWorkout) {
    // If the workout type hasn't changed, no need to proceed further
    return;
  }

  var currentTempo = document.getElementById("tempo").value;
  var currentEnergy = document.getElementById("energy").value;
  var currentDanceability = document.getElementById("danceability").value;
  var currentGenres = getSelectedGenres();

  // Define default values for the new workout
  var currentWorkoutDefaults = getDefaultValuesForWorkout(selectedWorkoutType);
  // Compare current state with default values
  if (
    currentTempo != currentWorkoutDefaults.tempo ||
    currentEnergy != currentWorkoutDefaults.energy ||
    currentDanceability != currentWorkoutDefaults.danceability ||
    !arraysEqual(currentGenres, currentWorkoutDefaults.genres)
  ) {
    showModal(newWorkout, onConfirm, onCancel);
  } else {
    // If no confirmation is needed, apply changes directly
    applyWorkoutChanges(newWorkout);
  }
}

// Function to apply the new workout changes
function applyWorkoutChanges(newWorkout) {
  selectedWorkoutType = newWorkout;

  var newWorkoutDefaults = getDefaultValuesForWorkout(newWorkout);

  document.getElementById("tempo").value = newWorkoutDefaults.tempo;
  document.getElementById("danceability").value = newWorkoutDefaults.danceability;
  document.getElementById("energy").value = newWorkoutDefaults.energy;

  updateTempoValue();

  // Update genres in the selected list
  getSelectedGenres().forEach((genre) => addOptionBackToDropdown(genre));
  updateGenresList(newWorkoutDefaults.genres);
  handleWorkoutSelection(newWorkout);
}

function getDefaultValuesForWorkout(workout) {
  switch (workout) {
    case "running":
      return {
        tempo: 90,
        danceability: 0.7,
        energy: 0.6,
        genres: ["Pop", "Rock", "Electronic"],
      };
    case "boxing":
      return {
        tempo: 130,
        danceability: 0.5,
        energy: 0.9,
        genres: ["Hip-Hop", "Rock", "Electronic"],
      };
    case "cycling":
      return {
        tempo: 140,
        danceability: 0.3,
        energy: 0.7,
        genres: ["EDM", "Rock", "Pop"],
      };
    case "yoga":
      return {
        tempo: 60,
        danceability: 0.1,
        energy: 0.2,
        genres: ["Ambient", "Classical", "Instrumental"],
      };
    case "gym":
      return {
        tempo: 130,
        danceability: 0.5,
        energy: 0.6,
        genres: ["Metal", "Rock", "Electronic"],
      };

    default:
      return {
        tempo: 100,
        danceability: 0.5,
        energy: 0.5,
        genres: [], // Default genres for 'general' or unknown workout types
      };
  }
}

function arraysEqual(arr1, arr2) {
  if (arr1.length !== arr2.length) return false;

  // Sort both arrays
  var sortedArr1 = arr1.slice().sort();
  var sortedArr2 = arr2.slice().sort();

  // Compare elements after sorting
  for (var i = 0; i < sortedArr1.length; i++) {
    if (sortedArr1[i] !== sortedArr2[i]) return false;
  }
  return true;
}

// Function to update the genres list based on selected default genres
function updateGenresList(defaultGenres) {
  // Clear existing selected genres
  clearSelectedGenres();

  // Add default genres to the selected list
  defaultGenres.forEach(function (genre) {
    addOptionToSelectedList(genre);
  });

  // Update the hidden input with selected genres
  updateHiddenInput();
}

// Function to clear the selected genres list
function clearSelectedGenres() {
  var selectedList = document.getElementById("selectedList");
  selectedList.innerHTML = "";
}

// Function to get a random integer within a range

// Event listener for changes in the workout selection
document.getElementsByName("workout").forEach(function (radio) {
  radio.addEventListener("change", function () {
    updateDefaultValues(this.value);
  });
});

function handleWorkoutSelection(workoutType) {
  // Remove existing workout class from body
  document.body.classList.remove("running", "boxing", "cycling", "yoga", "gym", "general");

  // Add the selected workout class to body
  document.body.classList.add(workoutType);
  updateSliderColours(workoutType);
}

function updateSliderColours(workoutType) {
  const sliders = document.querySelectorAll('input[type="range"]');
  const genPlaylistButton = document.getElementById("generatePlaylistButton");
  const metronomeButton = document.getElementById("metronome-button");
  const removeButtons = document.querySelectorAll(".remove");

  let backgroundColour;
  let buttonColour;
  let textColour;
  let removeColour;
  let hoverBackground;

  switch (workoutType) {
    case "running":
      backgroundColour = "linear-gradient(to right, #004d00, #00cc00)";
      buttonColour = "#00cc00";
      textColour = "#ffffff"; // White text for better visibility
      hoverBackground = "#009900";
      removeColour = "#0a3808";
      break;
    case "boxing":
      backgroundColour = "linear-gradient(to right, #8b008b, #e600e6)";
      buttonColour = "#e600e6";
      textColour = "#ffffff";
      hoverBackground = "#990099";
      removeColour = "#412275";
      break;
    case "cycling":
      backgroundColour = "linear-gradient(to right, #001f3f, #00BFFF)";
      buttonColour = "#00BFFF";
      textColour = "#ffffff";
      hoverBackground = "#007acc";
      removeColour = "#080d38";
      break;
    case "yoga":
      backgroundColour = "linear-gradient(to right, #b3b300, #ffff00)";
      buttonColour = "#b3b300";
      textColour = "#000000"; // Black text for better visibility
      hoverBackground = "#e6e600";
      removeColour = "#adad02";
      break;
    case "gym":
      backgroundColour = "linear-gradient(to right, #cc0000, #ff6600)";
      buttonColour = "#ff6600";
      textColour = "#ffffff";
      hoverBackground = "#ff3300";
      removeColour = "#7a0202";
      break;
    default:
      backgroundColour = "linear-gradient(to right, #636262, #ffffff)";
      buttonColour = "#ffffff";
      textColour = "#000000";
      hoverBackground = "#c0c0c0";
      removeColour = "#737373";
  }

  // Update background and text color of sliders
  sliders.forEach((slider) => {
    slider.style.background = backgroundColour;
  });

  // Update background and text color of the buttons
  genPlaylistButton.style.background = buttonColour;
  metronomeButton.style.background = buttonColour;

  genPlaylistButton.style.color = textColour;
  metronomeButton.style.color = textColour;

  // Add hover effect to the button
  genPlaylistButton.addEventListener("mouseover", function () {
    genPlaylistButton.style.background = hoverBackground;
  });

  genPlaylistButton.addEventListener("mouseout", function () {
    genPlaylistButton.style.background = buttonColour;
  });

  metronomeButton.addEventListener("mouseover", function () {
    metronomeButton.style.background = hoverBackground;
  });

  metronomeButton.addEventListener("mouseout", function () {
    metronomeButton.style.background = buttonColour;
  });
}

document.getElementById("inputForm").addEventListener("submit", function (event) {
  // Hide the submit button and show the loading animation
  const includeLikedSongsCheckbox = document.getElementById("includeLikedSongs");
  const includeLikedSongs = includeLikedSongsCheckbox.checked;

  if (includeLikedSongs) {
    document.getElementById("generatePlaylistButton").style.display = "none";
    document.getElementById("loading-container").style.display = "block";
  }
});

// Function to display the modal with callbacks
function showModal(newWorkout, onConfirm, onCancel) {
  var modal = document.getElementById("customModal");
  modal.style.display = "block";

  // Set up the confirm button
  document.getElementById("confirmBtn").onclick = function () {
    modal.style.display = "none";
    onConfirm(newWorkout); // Call the onConfirm callback with newWorkout
  };

  // Set up the cancel button
  document.getElementById("cancelBtn").onclick = function () {
    modal.style.display = "none";
    onCancel(); // Call the onCancel callback
  };
}

function revertWorkoutSelection() {
  if (previousSelectedWorkout !== null) {
    // Find and check the radio button corresponding to the previous workout
    var radioButton = document.querySelector(`input[name="workout"][value="${previousSelectedWorkout}"]`);
    if (radioButton) {
      radioButton.checked = true;
    }
  }
}
