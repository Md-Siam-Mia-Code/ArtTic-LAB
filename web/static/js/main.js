// web/static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
  // --- Application State ---
  const state = {
    isModelLoaded: false,
    isGenerating: false,
    isBusy: false, // General busy state for loading or generating
    modelType: "SD 1.5", // Default model type
    socket: null,
  };

  // --- DOM Element Cache ---
  const ui = {
    // Connection status
    connectionStatus: document.getElementById("connection-status"),
    // Pages and Navigation
    sidebarLinks: document.querySelectorAll(".sidebar-link"),
    pages: {
      generate: document.getElementById("page-generate"),
      gallery: document.getElementById("page-gallery"),
    },
    // Model Controls
    modelSelect: document.getElementById("model-select"),
    loadModelBtn: document.getElementById("load-model-btn"),
    unloadModelBtn: document.getElementById("unload-model-btn"),
    refreshModelsBtn: document.getElementById("refresh-models-btn"),
    statusText: document.getElementById("status-text"),
    // Generation Parameters
    prompt: document.getElementById("prompt"),
    negativePrompt: document.getElementById("negative-prompt"),
    stepsSlider: document.getElementById("steps-slider"),
    stepsValue: document.getElementById("steps-value"),
    guidanceSlider: document.getElementById("guidance-slider"),
    guidanceValue: document.getElementById("guidance-value"),
    widthSlider: document.getElementById("width-slider"),
    widthValue: document.getElementById("width-value"),
    heightSlider: document.getElementById("height-slider"),
    heightValue: document.getElementById("height-value"),
    aspectRatioBtns: document.getElementById("aspect-ratio-btns"),
    seedInput: document.getElementById("seed-input"),
    randomizeSeedBtn: document.getElementById("randomize-seed-btn"),
    // Advanced Options
    samplerSelect: document.getElementById("sampler-select"),
    vaeTilingCheckbox: document.getElementById("vae-tiling-checkbox"),
    cpuOffloadCheckbox: document.getElementById("cpu-offload-checkbox"),
    // Generation & Output
    generateBtn: document.getElementById("generate-btn"),
    outputImage: document.getElementById("output-image"),
    imagePlaceholder: document.getElementById("image-placeholder"),
    infoText: document.getElementById("info-text"),
    // Progress Bar
    progressContainer: document.getElementById("progress-container"),
    progressLabel: document.getElementById("progress-label"),
    progressPercent: document.getElementById("progress-percent"),
    progressBarFill: document.getElementById("progress-bar-fill"),
    // Gallery
    galleryGrid: document.getElementById("gallery-grid"),
    galleryPlaceholder: document.getElementById("gallery-placeholder"),
    refreshGalleryBtn: document.getElementById("refresh-gallery-btn"),
  };

  // --- Aspect Ratio Presets ---
  const ASPECT_RATIOS = {
    "SD 1.5": {
      "1:1": [512, 512],
      "4:3": [576, 448],
      "3:2": [608, 416],
      "16:9": [672, 384],
    },
    "SD 2.x": {
      "1:1": [768, 768],
      "4:3": [864, 640],
      "3:2": [960, 640],
      "16:9": [1024, 576],
    },
    SDXL: {
      "1:1": [1024, 1024],
      "4:3": [1152, 896],
      "3:2": [1216, 832],
      "16:9": [1344, 768],
    },
    SD3: {
      "1:1": [1024, 1024],
      "4:3": [1152, 896],
      "3:2": [1216, 832],
      "16:9": [1344, 768],
    },
  };

  // --- WebSocket Communication ---
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws`;
    state.socket = new WebSocket(url);

    state.socket.onopen = () => {
      console.log("WebSocket connected.");
      updateConnectionStatus("Connected", "connected");
    };

    state.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message.type, message.data);
    };

    state.socket.onclose = () => {
      console.warn("WebSocket disconnected. Attempting to reconnect...");
      updateConnectionStatus("Disconnected", "disconnected");
      setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
    };

    state.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      updateConnectionStatus("Error", "disconnected");
      state.socket.close();
    };
  }

  function sendMessage(action, payload = {}) {
    if (state.socket && state.socket.readyState === WebSocket.OPEN) {
      state.socket.send(JSON.stringify({ action, payload }));
    } else {
      console.error("WebSocket is not connected.");
    }
  }

  function handleWebSocketMessage(type, data) {
    switch (type) {
      case "model_loaded":
        state.isModelLoaded = true;
        state.modelType = data.model_type;
        updateStatus(data.status_message, "ready");
        setDimensions(data.width, data.height);
        setBusyState(false);
        break;
      case "generation_complete":
        ui.outputImage.src = `/outputs/${
          data.image_filename
        }?t=${new Date().getTime()}`;
        ui.outputImage.classList.remove("hidden");
        ui.imagePlaceholder.classList.add("hidden");
        ui.infoText.textContent = data.info;
        setBusyState(false, true);
        break;
      case "model_unloaded":
        state.isModelLoaded = false;
        updateStatus(data.status_message, "unloaded");
        setBusyState(false);
        break;
      case "progress_update":
        showProgressBar(true);
        ui.progressLabel.textContent = data.description;
        const percent = Math.round(data.progress * 100);
        ui.progressPercent.textContent = `${percent}%`;
        ui.progressBarFill.style.width = `${percent}%`;
        break;
      case "gallery_updated":
        populateGallery(data.images);
        break;
      case "error":
        alert(`An error occurred: ${data.message}`);
        setBusyState(false);
        break;
    }
  }

  // --- UI Update Functions ---
  function setBusyState(isBusy, isGeneration = false) {
    state.isBusy = isBusy;
    state.isGenerating = isBusy && isGeneration;

    // Toggle disabled state on all major controls
    const controls = [
      ui.loadModelBtn,
      ui.unloadModelBtn,
      ui.generateBtn,
      ui.modelSelect,
      ui.prompt,
      ui.negativePrompt,
      ui.stepsSlider,
      ui.guidanceSlider,
      ui.widthSlider,
      ui.heightSlider,
      ui.seedInput,
      ui.randomizeSeedBtn,
      ...ui.aspectRatioBtns.children,
    ];
    controls.forEach((el) => (el.disabled = isBusy));

    if (!isBusy) {
      showProgressBar(false);
      // Re-enable unload/generate based on model state
      ui.unloadModelBtn.disabled = !state.isModelLoaded;
      ui.generateBtn.disabled = !state.isModelLoaded;
    }
  }

  function updateStatus(message, statusClass) {
    ui.statusText.textContent = message;
    ui.statusText.className = `status-${statusClass}`;
  }

  function showProgressBar(show) {
    ui.progressContainer.classList.toggle("hidden", !show);
  }

  function updateConnectionStatus(text, statusClass) {
    ui.connectionStatus.textContent = text;
    ui.connectionStatus.className = `status-indicator-text ${statusClass}`;
  }

  function populateSelect(selectElement, options) {
    selectElement.innerHTML = "";
    options.forEach((option) => {
      const opt = document.createElement("option");
      opt.value = option;
      opt.textContent = option;
      selectElement.appendChild(opt);
    });
  }

  function populateGallery(images) {
    ui.galleryGrid.innerHTML = "";
    if (images && images.length > 0) {
      ui.galleryPlaceholder.classList.add("hidden");
      images.forEach((imageFile) => {
        const item = document.createElement("div");
        item.className = "gallery-item";
        item.innerHTML = `
                    <img src="/outputs/${imageFile}" alt="${imageFile}" class="gallery-item-image" loading="lazy">
                    <div class="gallery-item-overlay">
                        <div class="gallery-item-actions">
                            <a href="/outputs/${imageFile}" download class="gallery-item-action-btn" title="Download">
                                <span class="material-symbols-outlined">download</span>
                            </a>
                            <a href="/outputs/${imageFile}" target="_blank" class="gallery-item-action-btn" title="Open in New Tab">
                                <span class="material-symbols-outlined">open_in_new</span>
                            </a>
                        </div>
                    </div>
                `;
        ui.galleryGrid.appendChild(item);
      });
    } else {
      ui.galleryPlaceholder.classList.remove("hidden");
    }
  }

  function setDimensions(width, height) {
    ui.widthSlider.value = width;
    ui.widthValue.textContent = `${width}px`;
    ui.heightSlider.value = height;
    ui.heightValue.textContent = `${height}px`;
  }

  // --- Event Listeners ---
  function setupEventListeners() {
    // Slider value displays
    ["steps", "guidance", "width", "height"].forEach((id) => {
      const slider = ui[`${id}Slider`];
      const valueDisplay = ui[`${id}Value`];
      slider.addEventListener("input", () => {
        valueDisplay.textContent =
          id === "guidance"
            ? slider.value
            : `${slider.value}${id.includes("Slider") ? "" : "px"}`;
        if (id === "width" || id === "height") {
          valueDisplay.textContent += "px";
        }
      });
    });

    // Navigation
    ui.sidebarLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = `page-${link.dataset.target}`;

        // Update active link
        ui.sidebarLinks.forEach((l) => l.classList.remove("active"));
        link.classList.add("active");

        // Show target page, hide others
        Object.values(ui.pages).forEach((page) => {
          page.id === targetId
            ? page.classList.remove("hidden")
            : page.classList.add("hidden");
        });
      });
    });

    // Model Actions
    ui.loadModelBtn.addEventListener("click", () => {
      setBusyState(true);
      updateStatus("Loading model...", "busy");
      showProgressBar(true);
      sendMessage("load_model", {
        model_name: ui.modelSelect.value,
        scheduler_name: ui.samplerSelect.value,
        vae_tiling: ui.vaeTilingCheckbox.checked,
        cpu_offload: ui.cpuOffloadCheckbox.checked,
      });
    });

    ui.unloadModelBtn.addEventListener("click", () => {
      setBusyState(true);
      updateStatus("Unloading model...", "busy");
      sendMessage("unload_model");
    });

    ui.refreshModelsBtn.addEventListener("click", () => init());

    // Generation Actions
    ui.generateBtn.addEventListener("click", () => {
      setBusyState(true, true);
      ui.infoText.textContent = "";
      showProgressBar(true);
      sendMessage("generate_image", {
        prompt: ui.prompt.value,
        negative_prompt: ui.negativePrompt.value,
        steps: parseInt(ui.stepsSlider.value),
        guidance: parseFloat(ui.guidanceSlider.value),
        seed: parseInt(ui.seedInput.value),
        width: parseInt(ui.widthSlider.value),
        height: parseInt(ui.heightSlider.value),
      });
    });

    ui.randomizeSeedBtn.addEventListener("click", () => {
      ui.seedInput.value = Math.floor(Math.random() * 2 ** 32);
    });

    ui.aspectRatioBtns.addEventListener("click", (e) => {
      const btn = e.target.closest(".btn-aspect-ratio");
      if (btn && !state.isBusy) {
        const ratio = btn.dataset.ratio;
        const presets =
          ASPECT_RATIOS[state.modelType] || ASPECT_RATIOS["SD 1.5"];
        if (presets[ratio]) {
          setDimensions(...presets[ratio]);
          // Update active button style
          ui.aspectRatioBtns
            .querySelectorAll("button")
            .forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
        }
      }
    });

    // Gallery Actions
    ui.refreshGalleryBtn.addEventListener("click", () => {
      // Re-fetch initial config to get the latest gallery
      init();
    });
  }

  // --- Initialization ---
  async function init() {
    try {
      const response = await fetch("/api/config");
      const config = await response.json();

      populateSelect(ui.modelSelect, config.models);
      populateSelect(ui.samplerSelect, config.schedulers);
      populateGallery(config.gallery_images);

      // Set initial state
      setBusyState(false);
    } catch (error) {
      console.error("Failed to fetch initial config:", error);
      alert("Could not load initial configuration from the server.");
    }
  }

  // Start the application
  init();
  connectWebSocket();
  setupEventListeners();
});
