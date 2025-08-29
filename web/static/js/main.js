// web/static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
  // --- Application State & Constants ---
  const state = {
    isModelLoaded: false,
    isBusy: false,
    modelType: "SD 1.5",
    socket: null,
  };
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

  // --- DOM Element Cache (Complete) ---
  const ui = {
    nav: { links: document.querySelectorAll(".nav-link") },
    pages: {
      generate: document.getElementById("page-generate"),
      gallery: document.getElementById("page-gallery"),
    },
    status: {
      indicator: document.getElementById("status-indicator"),
      connectionText: document.getElementById("connection-status"),
      card: document.getElementById("status-card"),
      text: document.getElementById("status-text"),
      icon: document.querySelector("#status-card .material-symbols-outlined"),
    },
    model: {
      dropdown: document.getElementById("model-dropdown"),
      samplerDropdown: document.getElementById("sampler-dropdown"),
      loadBtn: document.getElementById("load-model-btn"),
      unloadBtn: document.getElementById("unload-model-btn"),
    },
    params: {
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
      vaeTilingCheckbox: document.getElementById("vae-tiling-checkbox"),
      cpuOffloadCheckbox: document.getElementById("cpu-offload-checkbox"),
    },
    generate: {
      btn: document.getElementById("generate-btn"),
      outputImage: document.getElementById("output-image"),
      imagePlaceholder: document.getElementById("image-placeholder"),
      infoText: document.getElementById("info-text"),
      downloadBtn: document.getElementById("download-btn"),
      openNewTabBtn: document.getElementById("open-new-tab-btn"),
    },
    progress: {
      container: document.getElementById("progress-container"),
      label: document.getElementById("progress-label"),
      percent: document.getElementById("progress-percent"),
      barFill: document.getElementById("progress-bar-fill"),
    },
    gallery: {
      grid: document.getElementById("gallery-grid"),
      placeholder: document.getElementById("gallery-placeholder"),
      refreshBtn: document.getElementById("refresh-gallery-btn"),
    },
    lightbox: {
      container: document.getElementById("lightbox"),
      closeBtn: document.getElementById("lightbox-close"),
      img: document.getElementById("lightbox-img"),
      caption: document.getElementById("lightbox-caption"),
    },
  };

  // --- WebSocket Communication ---
  function connectWebSocket() {
    const url = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${
      window.location.host
    }/ws`;
    state.socket = new WebSocket(url);
    state.socket.onopen = () =>
      updateConnectionStatus("Connected", "connected");
    state.socket.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);
      handleWebSocketMessage(type, data);
    };
    state.socket.onclose = () => {
      updateConnectionStatus("Reconnecting...", "connecting");
      setTimeout(connectWebSocket, 3000);
    };
    state.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      updateConnectionStatus("Error", "disconnected");
      state.socket.close();
    };
  }

  function sendMessage(action, payload = {}) {
    if (state.socket?.readyState === WebSocket.OPEN) {
      state.socket.send(JSON.stringify({ action, payload }));
    }
  }

  const messageHandlers = {
    model_loaded: (data) => {
      state.isModelLoaded = true;
      state.modelType = data.model_type;
      updateStatus(data.status_message, "ready");
      setDimensions(data.width, data.height);
      setBusyState(false);
    },
    generation_complete: (data) => {
      const imageUrl = `/outputs/${data.image_filename}?t=${Date.now()}`;
      ui.generate.outputImage.src = imageUrl;
      ui.generate.downloadBtn.href = imageUrl;
      ui.generate.openNewTabBtn.href = imageUrl;
      ui.generate.outputImage.classList.remove("hidden");
      ui.generate.imagePlaceholder.classList.add("hidden");
      ui.generate.infoText.textContent = data.info;
      setBusyState(false);
    },
    model_unloaded: (data) => {
      state.isModelLoaded = false;
      updateStatus(data.status_message, "unloaded");
      setBusyState(false);
    },
    progress_update: (data) => {
      showProgressBar(true);
      ui.progress.label.textContent = data.description;
      const percent = Math.round(data.progress * 100);
      ui.progress.percent.textContent = `${percent}%`;
      ui.progress.barFill.style.width = `${percent}%`;
    },
    gallery_updated: (data) => populateGallery(data.images),
    error: (data) => {
      alert(`An error occurred: ${data.message}`);
      setBusyState(false);
    },
  };

  function handleWebSocketMessage(type, data) {
    (
      messageHandlers[type] ||
      (() => console.warn(`Unhandled message type: ${type}`))
    )(data);
  }

  // --- UI Update & Control Functions ---
  function setBusyState(isBusy) {
    state.isBusy = isBusy;
    document.body.style.cursor = isBusy ? "wait" : "default";
    if (!isBusy) showProgressBar(false);
    document
      .querySelectorAll("button, input, textarea, .custom-dropdown")
      .forEach((el) => {
        el.classList.toggle("disabled", isBusy);
        if (el.tagName !== "DIV") el.disabled = isBusy; // Don't disable divs
      });
    if (!isBusy) {
      ui.model.unloadBtn.disabled = !state.isModelLoaded;
      ui.generate.btn.disabled = !state.isModelLoaded;
    }
  }

  function updateStatus(message, statusClass) {
    ui.status.text.textContent = message;
    const iconName =
      { ready: "memory", unloaded: "memory_off", busy: "hourglass_top" }[
        statusClass
      ] || "memory";
    const className = `material-symbols-outlined icon-${statusClass}`;
    ui.status.icon.textContent = iconName;
    ui.status.icon.className = className;
  }

  function showProgressBar(show) {
    ui.progress.container.classList.toggle("hidden", !show);
  }
  function updateConnectionStatus(text, statusClass) {
    ui.status.connectionText.textContent = text;
    ui.status.indicator.className = `status-indicator ${statusClass}`;
  }

  function setDimensions(width, height) {
    ui.params.widthSlider.value = width;
    ui.params.heightSlider.value = height;
    // Trigger input event to update UI
    ui.params.widthSlider.dispatchEvent(new Event("input"));
    ui.params.heightSlider.dispatchEvent(new Event("input"));
  }

  // --- Custom Components ---
  function createCustomDropdown(container, options, onSelect) {
    container.innerHTML = `<div class="dropdown-selected" tabindex="0"><span class="selected-text">${
      options[0] || "No options"
    }</span></div><ul class="dropdown-options"></ul>`;
    const selected = container.querySelector(".selected-text");
    const optionsList = container.querySelector(".dropdown-options");
    options.forEach((option) => {
      const li = document.createElement("li");
      li.className = "dropdown-option";
      li.textContent = option;
      li.dataset.value = option;
      optionsList.appendChild(li);
    });
    container.dataset.value = options[0] || "";
    if (options[0]) optionsList.querySelector("li").classList.add("selected");
    container.addEventListener("click", (e) => {
      if (!container.classList.contains("disabled")) {
        e.stopPropagation();
        container.classList.toggle("open");
      }
    });
    optionsList.addEventListener("click", (e) => {
      if (e.target.tagName === "LI") {
        container.dataset.value = e.target.dataset.value;
        selected.textContent = e.target.textContent;
        optionsList
          .querySelectorAll("li")
          .forEach((li) => li.classList.remove("selected"));
        e.target.classList.add("selected");
        onSelect?.(e.target.dataset.value);
      }
    });
  }

  function populateGallery(images) {
    ui.gallery.grid.innerHTML = "";
    const hasImages = images?.length > 0;
    ui.gallery.placeholder.classList.toggle("hidden", hasImages);
    if (hasImages) {
      images.forEach((imageFile) => {
        const item = document.createElement("div");
        item.className = "gallery-item";
        const imageUrl = `/outputs/${imageFile}`;
        item.innerHTML = `<img src="${imageUrl}" alt="${imageFile}" class="gallery-item-image" loading="lazy"><div class="image-actions-overlay"><a href="${imageUrl}" download class="image-action-btn" title="Download Image"><span class="material-symbols-outlined">download</span></a><a href="${imageUrl}" target="_blank" class="image-action-btn" title="Open in New Tab"><span class="material-symbols-outlined">open_in_new</span></a></div>`;
        item
          .querySelector(".image-actions-overlay")
          .addEventListener("click", (e) => e.stopPropagation());
        item.addEventListener("click", () => openLightbox(imageUrl, imageFile));
        ui.gallery.grid.appendChild(item);
      });
    }
  }

  function openLightbox(src, caption) {
    ui.lightbox.img.src = src;
    ui.lightbox.caption.textContent = caption;
    ui.lightbox.container.classList.remove("hidden");
  }

  function updateSliderBackground(slider) {
    const min = parseFloat(slider.min || 0);
    const max = parseFloat(slider.max || 100);
    const val = parseFloat(slider.value);
    const percentage = ((val - min) * 100) / (max - min);
    slider.style.backgroundSize = `${percentage}% 100%`;
  }

  // --- Event Listeners Setup ---
  function setupEventListeners() {
    document.querySelectorAll(".range-input").forEach((slider) => {
      // *** FIX IS HERE ***
      // Correctly derive the value-display ID from the slider ID
      const valueDisplayId = slider.id.replace("-slider", "-value");
      const valueDisplay = document.getElementById(valueDisplayId);

      const updateFunc = () => {
        const suffix =
          slider.id.includes("width") || slider.id.includes("height")
            ? "px"
            : "";
        if (valueDisplay) {
          // Check if the element exists before trying to set its content
          valueDisplay.textContent = slider.value + suffix;
        }
        updateSliderBackground(slider);
      };
      slider.addEventListener("input", updateFunc);
      updateFunc(); // Initial call
    });

    ui.nav.links.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        ui.nav.links.forEach((l) => l.classList.remove("active"));
        link.classList.add("active");
        Object.values(ui.pages).forEach((page) => page.classList.add("hidden"));
        document
          .getElementById(`page-${link.dataset.target}`)
          .classList.remove("hidden");
      });
    });

    ui.model.loadBtn.addEventListener("click", () => {
      setBusyState(true);
      updateStatus("Loading model...", "busy");
      sendMessage("load_model", {
        model_name: ui.model.dropdown.dataset.value,
        scheduler_name: ui.model.samplerDropdown.dataset.value,
        vae_tiling: ui.params.vaeTilingCheckbox.checked,
        cpu_offload: ui.params.cpuOffloadCheckbox.checked,
      });
    });

    ui.model.unloadBtn.addEventListener("click", () => {
      setBusyState(true);
      updateStatus("Unloading model...", "busy");
      sendMessage("unload_model");
    });

    ui.generate.btn.addEventListener("click", () => {
      setBusyState(true);
      ui.generate.infoText.textContent = "";
      sendMessage("generate_image", {
        prompt: ui.params.prompt.value,
        negative_prompt: ui.params.negativePrompt.value,
        steps: parseInt(ui.params.stepsSlider.value),
        guidance: parseFloat(ui.params.guidanceSlider.value),
        seed: parseInt(ui.params.seedInput.value),
        width: parseInt(ui.params.widthSlider.value),
        height: parseInt(ui.params.heightSlider.value),
      });
    });

    ui.params.randomizeSeedBtn.addEventListener("click", () => {
      ui.params.seedInput.value = Math.floor(Math.random() * 2 ** 32);
    });

    ui.params.aspectRatioBtns.addEventListener("click", (e) => {
      const btn = e.target.closest(".btn-aspect-ratio");
      if (btn && !state.isBusy) {
        const ratio = btn.dataset.ratio;
        const presets =
          ASPECT_RATIOS[state.modelType] || ASPECT_RATIOS["SD 1.5"];
        if (presets[ratio]) {
          setDimensions(...presets[ratio]);
          ui.params.aspectRatioBtns
            .querySelectorAll("button")
            .forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
        }
      }
    });

    ui.gallery.refreshBtn.addEventListener("click", () =>
      fetch("/api/config")
        .then((res) => res.json())
        .then((config) => populateGallery(config.gallery_images))
    );

    ui.lightbox.closeBtn.addEventListener("click", () =>
      ui.lightbox.container.classList.add("hidden")
    );
    ui.lightbox.container.addEventListener("click", (e) => {
      if (e.target === ui.lightbox.container)
        ui.lightbox.container.classList.add("hidden");
    });
  }

  // --- Initialization ---
  async function init() {
    try {
      const response = await fetch("/api/config");
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const config = await response.json();
      createCustomDropdown(ui.model.dropdown, config.models);
      createCustomDropdown(ui.model.samplerDropdown, config.schedulers);
      populateGallery(config.gallery_images);
      setBusyState(false);
    } catch (error) {
      console.error("Failed to fetch initial config:", error);
      alert("Could not load configuration from the server. Please refresh.");
    }
  }

  init();
  connectWebSocket();
  setupEventListeners();
  document.addEventListener("click", () =>
    document
      .querySelectorAll(".custom-dropdown.open")
      .forEach((d) => d.classList.remove("open"))
  );
});
