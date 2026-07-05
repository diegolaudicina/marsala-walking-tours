/* Initialize Bootstrap Tooltips */
document.addEventListener("DOMContentLoaded", function () {
    var tooltipTriggerList = [...document.querySelectorAll('[data-bs-toggle="tooltip"]')];
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});


/* Auto-dismiss Flash Messages after 5 seconds */
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        var alertNodeList = [...document.querySelectorAll('.flash-notif')];
        alertNodeList.forEach(function (alertNode) {
            var alert = new bootstrap.Alert(alertNode);
            alert.close();
        });
    }, 5000);
});

/*
Function toggleRegistrationForm
    Used on page 'register.html' to change registration mode from 'guide' to 'participant' and viceversa
    If toggled, hides the 'guide' registration form, showing the 'participant' one and changing the heading accordingly
    Default visibility value is 'guide'
*/

function toggleRegistrationForm() {
    const isGuide = document.getElementById('btn-guide').checked;
    const guideForm = document.getElementById('guide-form-container');
    const participantForm = document.getElementById('participant-form-container');
    const formTitle = document.getElementById('form-title');

    if (isGuide) {
        guideForm.classList.remove('d-none');
        participantForm.classList.add('d-none');
        formTitle.textContent = 'Register as a guide';
    } else {
        guideForm.classList.add('d-none');
        participantForm.classList.remove('d-none');
        formTitle.textContent = 'Register as a participant';
    }
}

/* Function toggleLoginForm
    Same as toggleRegistrationForm, but for page 'login.html' */

function toggleLoginForm() {
    const isGuide = document.getElementById('btn-guide').checked;
    const guideForm = document.getElementById('guide-form-container');
    const participantForm = document.getElementById('participant-form-container');
    const formTitle = document.getElementById('form-title');

    if (isGuide) {
        guideForm.classList.remove('d-none');
        participantForm.classList.add('d-none');
        formTitle.textContent = 'Login as a guide'
    } else {
        guideForm.classList.add('d-none');
        participantForm.classList.remove('d-none');
        formTitle.textContent = 'Login as a participant'
    }
}

/* 
Logic for page 'create_tour.html'
    Enables/disables time inputs based on day checkboxes and restricts photo uploads with less than 5 photos
*/
document.addEventListener("DOMContentLoaded", function () {
    const dayCheckboxes = document.querySelectorAll('.day-checkbox');
    if (dayCheckboxes.length > 0) {
        dayCheckboxes.forEach(function (checkbox) {
            checkbox.addEventListener('change', function () {
                const timeInput = document.getElementById('time_' + this.value);
                if (this.checked) {
                    timeInput.disabled = false;
                    timeInput.required = true;
                } else {
                    timeInput.disabled = true;
                    timeInput.required = false;
                    timeInput.value = '';
                }
            });
        });
    }

    const photosInput = document.getElementById('photos');
    const photoFeedback = document.getElementById('photo_feedback');
    const clearPhotosBtn = document.getElementById('clearPhotosBtn');

    if (photosInput && photoFeedback) {
        if (clearPhotosBtn) {
            clearPhotosBtn.addEventListener('click', function () {
                photosInput.value = '';
                const event = new Event('change');
                photosInput.dispatchEvent(event);
            });
        }

        function validatePhotos() {
            const numFiles = photosInput.files.length;
            const isEdit = !photosInput.hasAttribute('required');

            if (clearPhotosBtn) {
                if (numFiles > 0) {
                    clearPhotosBtn.classList.remove('d-none');
                } else {
                    clearPhotosBtn.classList.add('d-none');
                }
            }

            if (isEdit) {
                if (numFiles > 0 && numFiles !== 5) {
                    photosInput.setCustomValidity("You have to upload exactly 5 images, or none to keep the original ones.");
                    photoFeedback.innerHTML = '<span class="text-danger fw-bold">You have to upload exactly 5 images, or none.</span>';
                } else if (numFiles === 5) {
                    photosInput.setCustomValidity("");
                    photoFeedback.innerHTML = '<span class="text-success">You selected ' + numFiles + ' photos.</span>';
                } else {
                    photosInput.setCustomValidity("");
                    photoFeedback.innerHTML = 'No photos selected. Existing photos will be kept.';
                    photoFeedback.classList.remove('text-danger', 'fw-bold');
                }
            } else {
                if (numFiles !== 5 && numFiles > 0) {
                    photosInput.setCustomValidity("You have to select exactly 5 images.");
                    photoFeedback.innerHTML = '<span class="text-danger fw-bold">You have to select exactly 5 images.</span>';
                } else if (numFiles === 5) {
                    photosInput.setCustomValidity("");
                    photoFeedback.innerHTML = '<span class="text-success">You selected ' + numFiles + ' photos.</span>';
                } else {
                    photosInput.setCustomValidity("");
                    photoFeedback.innerHTML = 'No photos selected.';
                    photoFeedback.classList.remove('text-danger', 'fw-bold');
                }
            }
        }

        photosInput.addEventListener('change', validatePhotos);

        const form = photosInput.closest('form');
        if (form) {
            form.addEventListener('submit', function (e) {
                validatePhotos();
                if (!photosInput.checkValidity()) {
                    e.preventDefault();
                }
            });
        }
    }
});

/* Logic for stops text fields and add stop buttons */
document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("stops-container");
    const addBtn = document.getElementById("add-stop-btn");

    //Error avoiding code line
    if (!container || !addBtn) return;

    function updateStops() {
        const entries = container.querySelectorAll(".stop-entry");
        entries.forEach((entry, index) => {
            entry.querySelector(".input-group-text").textContent = index + 1;
            const removeBtn = entry.querySelector(".remove-stop-btn");
            if (entries.length <= 4) {
                removeBtn.disabled = true;
            } else {
                removeBtn.disabled = false;
            }
        });
    }

    addBtn.addEventListener("click", function () {
        const newEntry = document.createElement("div");
        newEntry.className = "input-group mb-2 stop-entry";
        newEntry.innerHTML = `
            <span class="input-group-text"></span>
            <input type="text" class="form-control" name="stops" placeholder="Next stop" required>
            <button class="btn btn-outline-danger remove-stop-btn" type="button">Remove</button>
        `;
        container.appendChild(newEntry);
        updateStops();
    });

    container.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-stop-btn")) {
            const entry = e.target.closest(".stop-entry");
            if (container.querySelectorAll(".stop-entry").length > 4) {
                entry.remove();
                updateStops();
            }
        }
    });

    // Initialize state
    updateStops();
});



/*
    Logic for page "book_tour.html"
    Handles the extra participant logic and all the costraints
*/

document.addEventListener("DOMContentLoaded", function () {
    const dateSelect = document.getElementById("booking_date");
    const addPersonBtn = document.getElementById("addPersonBtn");
    const removePersonBtn = document.getElementById("removePersonBtn");

    //Error avoiding code line
    if (!dateSelect) return;

    let currentAdded = 0; // how many extra people are currently shown

    function updateAvailability() {
        // Get selected option
        const selectedOption = dateSelect.options[dateSelect.selectedIndex];
        // If no date is selected, the "Add person" button is hidden and the script stops
        if (!selectedOption.value) {
            addPersonBtn.classList.add('d-none');
            addPersonBtn.classList.remove('d-inline-block');
            if (removePersonBtn) {
                removePersonBtn.classList.add('d-none');
                removePersonBtn.classList.remove('d-inline-block');
            }
            return;
        }

        //Retrieving available spots (saved in 'data-spots')
        const availableSpots = parseInt(selectedOption.getAttribute("data-spots"));

        // Available extra spots (total spots - 1 for the current user)
        // 3 extra people maximum
        const maxExtra = Math.min(3, availableSpots - 1);

        // Hide rows that exceed new maxExtra, clearing their values
        for (let i = 1; i <= 3; i++) {
            const row = document.getElementById("person_" + i + "_row");
            if (i > maxExtra) {
                row.classList.add('d-none');
                row.classList.remove('d-flex');
                row.querySelectorAll('input').forEach(input => {
                    input.value = "";
                    input.required = false;
                });
                if (currentAdded >= i) currentAdded = maxExtra;
            }
        }

        // Show/hide "Add person" button
        if (currentAdded < maxExtra) {
            addPersonBtn.classList.remove('d-none');
            addPersonBtn.classList.add('d-inline-block');
        } else {
            addPersonBtn.classList.add('d-none');
            addPersonBtn.classList.remove('d-inline-block');
        }

        // Show/hide "Remove person" button
        if (currentAdded > 0) {
            removePersonBtn.classList.remove('d-none');
            removePersonBtn.classList.add('d-inline-block');
        } else {
            removePersonBtn.classList.add('d-none');
            removePersonBtn.classList.remove('d-inline-block');
        }
    }

    // When date changes, update spots
    dateSelect.addEventListener("change", function () {
        // Reset additional participants if date changes
        currentAdded = 0;
        for (let i = 1; i <= 3; i++) {
            const row = document.getElementById("person_" + i + "_row");
            row.classList.add('d-none');
            row.classList.remove('d-flex');
            row.querySelectorAll('input').forEach(input => {
                input.value = "";
                input.required = false;
            });
        }
        updateAvailability();
    });

    // Add person button click
    addPersonBtn.addEventListener("click", function () {
        const selectedOption = dateSelect.options[dateSelect.selectedIndex];
        const availableSpots = parseInt(selectedOption.getAttribute("data-spots"));
        const maxExtra = Math.min(3, availableSpots - 1);

        if (currentAdded < maxExtra) {
            currentAdded++;
            const row = document.getElementById("person_" + currentAdded + "_row");
            row.classList.remove('d-none');
            row.classList.add('d-flex');
            // make inputs required when shown
            row.querySelectorAll('input').forEach(input => input.required = true);
        }

        //Calculating availability to decide whether to hide or not the "Add person" button
        updateAvailability();
    });

    // Remove person button click event
    if (removePersonBtn) {
        removePersonBtn.addEventListener("click", function () {
            if (currentAdded > 0) {
                const row = document.getElementById("person_" + currentAdded + "_row");

                row.classList.add('d-none');
                row.classList.remove('d-flex');

                row.querySelectorAll('input').forEach(input => {
                    input.value = "";
                    input.required = false;
                });

                currentAdded--;
                updateAvailability();
            }
        });
    }

    // Check if there are already filled extra participants (e.g. edit mode)
    for (let i = 1; i <= 3; i++) {
        let inputFirst = document.querySelector('input[name="person_' + i + '_first"]');
        if (inputFirst && inputFirst.value.trim() !== '') {
            currentAdded = i;
            const row = document.getElementById("person_" + i + "_row");
            row.classList.remove('d-none');
            row.classList.add('d-flex');
            row.querySelectorAll('input').forEach(input => input.required = true);
        }
    }

    // Initial setup on page load (in case a date is pre-selected)
    if (dateSelect && dateSelect.value) {
        updateAvailability();
    }
});

