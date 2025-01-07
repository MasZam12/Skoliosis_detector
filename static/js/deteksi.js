document.getElementById("upload-button").addEventListener("click", function () {
  document.getElementById("upload").click();
});

document.getElementById("upload").addEventListener("change", function (event) {
  const file = event.target.files[0];
  if (file) {
    console.log("File yang dipilih:", file.name);

    const allowedTypes = ["image/jpeg", "image/png"];
    if (!allowedTypes.includes(file.type)) {
      alert("Harap unggah file gambar (JPG atau PNG)!");
      return;
    }

    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      alert("Ukuran file terlalu besar! Maksimum 5 MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      const imageContainer = document.querySelector(".image_container");

      const svgElement = imageContainer.querySelector("svg");
      if (svgElement) {
        svgElement.style.display = "none";
        console.log("asu");
      }

      const imgTag = document.createElement("img");
      imgTag.src = e.target.result;
      imgTag.alt = "Uploaded Image";
      imgTag.style.width = "100%";

      const existingImg = imageContainer.querySelector("img");
      if (existingImg) {
        existingImg.remove();
      }

      imageContainer.appendChild(imgTag);
    };
    reader.readAsDataURL(file);
  }
});

document
  .getElementById("periksa-button")
  .addEventListener("click", function () {
    const fileInput = document.getElementById("upload");
    if (!fileInput.files.length) {
      alert("Harap unggah gambar terlebih dahulu!");
    } else {
      const periksaButton = document.getElementById("periksa-button");
      periksaButton.disabled = true;
      periksaButton.textContent = "Memproses...";

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      // Mengirim file ke server
      fetch("http://localhost:3000/api/upload", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);

          document.getElementById("edge-image").src = data.edges_url;
          document.getElementById("histogram-image").src = data.blurred_url;
          document.getElementById("segment-image").src = data.equalized_url;
          document.getElementById("diagnosis-image").src = data.result_url;
          document.getElementById("angle").textContent = data.angle;
          document.getElementById("hasil").innerHTML = `
              <div class="angle" id="angle">
                <p>Angle: ${data.angle}</p>
              </div>
              <div class="hasil-diagnosa" id="hasil-diagnosa">
                <p>Hasil Diagnosis: ${data.diagnosis}</p>
              </div>
            </div>
          `;

          console.log(data.diagnosis);
        })

        .catch((error) => {
          console.error("Terjadi kesalahan saat mengirim file:", error);
          alert(
            "Gagal mengunggah file. Pastikan server sedang berjalan dan coba lagi."
          );
        })
        .finally(() => {
          periksaButton.disabled = false;
          periksaButton.textContent = "Periksa";
        });
    }
  });
