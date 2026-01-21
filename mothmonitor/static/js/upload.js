const ALLOWED_IMAGE_TYPES = ["image/jpeg"]

const ALLOWED_OTHER_TYPES = ["application/zip", "application/json", "text/csv"]

const NO_NIGHT = "ZZZZ"

const fileRE = /(?<device>[^_]*)_(?<year>\d\d\d\d)_(?<month>\d\d)_(?<day>\d\d)/

function build_manifest(device, night, files) {
  return {
    deviceName: device,
    night: night,
    files: Array.from(files).map(x => {
      return {
        filename: x.name,
        size: x.size,
        type: x.type
      }
    })
  }
}

function validate_directory(files) {
  let res = {
    device: "",
    night: NO_NIGHT,
    errors: [],
    checks: []
  };
  let pathRoots = new Set();
  let images = [];
  let dates = new Set();
  for (let file of files) {
    if (file.webkitRelativePath) {
      pathRoots.add(file.webkitRelativePath.split("/").slice(0, -1).join("/"));
    }
    if (ALLOWED_IMAGE_TYPES.includes(file.type)) {
      images.push(file);
    }
    let match = fileRE.exec(file.name)
    if (match) {
      res.device = match.groups.device;
      let date = `${match.groups.year}-${match.groups.month}-${match.groups.day}`;
      dates.add(date);
      if (date < res.night) {
        res.night = date;
      }
    }
  }
  if (images.length < 1) {
    res.errors.push("None of these files are images.");
  }
  else if (images.length < (files.length * 0.5)) {
    res.errors.push("Most of these files are not images?");
  }
  if(pathRoots.size > 1) {
    res.errors.push("Too many directories: "+Array.from(pathRoots));
  }
  if(dates.size > 2) {
    res.errors.push("Too many nights: "+Array.from(dates));
  }
  if(!res.device) {
    res.errors.push("Couldn't find a device from image names.")
  }
  if(res.night == NO_NIGHT) {
    res.errors.push("Couldn't find a nightly date from image names.")
    res.night = "";
  }
  
  res.checks.push(files.length+" files selected.")
  return res;
}

function directory_handler(ev) {
  reset();
  let files = ev.target.files;
  let valid = validate_directory(files);

  valid.errors.map(x => show_step_message("validate", "error", x))
  valid.checks.map(x => show_step_message("validate", "ok", x))

  document.getElementById("deviceName").value = valid.device;
  document.getElementById("night").value = valid.night;
  
  show("validate");
}

function show_step_message(step, cls, msg) {
  let el = document.querySelector(".upload-"+step+" ul");
  if (el) {
    let li = document.createElement('li');
    li.textContent = msg;
    li.classList.add(cls)
    el.append(li)
  }  
}

async function upload_start(ev) {
  ev.preventDefault();
  ev.stopPropagation();
  let spinner = ev.target.querySelector(".spinner");
  spinner.classList.remove("hidden");

  let device = document.getElementById("deviceName").value;
  let night = document.getElementById("night").value;
  let files = document.getElementById("uploadDir").files;
  
  let manifest = build_manifest(device, night, files);
  ev.target.disabled = true;
  try {
    let resp = await fetch("/upload/check_manifest", {
      method: "POST",
      body: JSON.stringify(manifest),
      headers: {
        "Content-Type": "application/json"
      }
    })

    spinner.classList.add("hidden");
    show("manifest")

    let body = await resp.json()

    let needed = body.files.filter(x => x["missing"])
    let previous = body.files.length-needed.length
    console.log("needed", needed, "previous", previous)
    let msg = needed.length+" new files to upload. ";
    if (previous > 0) {
      msg += previous+" previously uploaded.";
    }
    show_step_message("manifest", "ok", msg)

    let progress = document.getElementById("upload_progress");
    let remainingEl = document.getElementById("remainingFiles");
    let neededEl = document.getElementById("neededFiles");

    let count = needed.length;
    let up = 0;

    neededEl.textContent = count;
    progress.max = count;

    show("progress")

    for (let f of needed) {
      // upload to S3 url
      await new Promise(r => setTimeout(r, 2000));
      up++;
      remainingEl.textContent = up;
      progress.value = up;
    }
  }
  catch(e) {
    ev.target.disabled = false;
    throw(e)
  }
    
  show("finished")
  
  
}

function reset() {
  document.querySelectorAll(".upload-validate, .upload-manifest, .upload-progress, .upload-finished").forEach((x) => {
    x.classList.add("hidden");
  })
  for (let el of document.querySelectorAll(".upload-validate ul, .upload-progress ul")) {
    el.replaceChildren();
  }
  document.querySelectorAll(".upload-start").forEach((x) => {
    x.disabled = false;
  })
  document.getElementById("deviceName").value = "";
  document.getElementById("night").value = "";
  
}

function show(step) {
  document.querySelectorAll(".upload-"+step).forEach((x) => {
    x.classList.remove("hidden");
  }) 
  
}

window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll(".upload-dir").forEach((x) => {
    x.addEventListener("change", directory_handler);
  })
  document.querySelectorAll(".upload-start").forEach((x) => {
    x.addEventListener("click", upload_start);
  })
});
