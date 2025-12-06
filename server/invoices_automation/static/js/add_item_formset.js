document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("materials-container");
    const addBtn = document.getElementById("add-material");
    const totalForms = document.getElementById("id_items-TOTAL_FORMS");

    const emptyFormEl = document.getElementById("empty-form").innerHTML;

    addBtn.addEventListener("click", function () {
        const formIdx = parseInt(totalForms.value, 10);

        // Create a new form replacing the __prefix__ by the index
        const newFormHtml = emptyFormEl.replace(/__prefix__/g, formIdx);

        const wrapper = document.createElement("div");
        wrapper.classList.add("material-item-form");
        wrapper.innerHTML = newFormHtml;

        container.appendChild(wrapper);

        totalForms.value = formIdx + 1;
    });

    container.addEventListener("click", function (event) {
        // Remove new forms and (or) mark existing ones for deletion
        if (event.target.classList.contains("remove-material") ||
            event.target.classList.contains("remove-material-persistent")) {

            const item = event.target.closest(".material-item-form");

            let deleteInput = item.querySelector('input[name$="-DELETE"]');

            if (deleteInput) {
                if (deleteInput.type === "checkbox") {
                    deleteInput.checked = true;
                } else {
                    deleteInput.value = "on";
                }

                // Hide the form visually
                item.style.display = "none";
                return;
            }

            const anyInput = item.querySelector('input[name], select[name], textarea[name]');
            if (!anyInput) {
                item.remove();
                return;
            }

            const name = anyInput.getAttribute('name');
            const m = name.match(/^(.+?-\d+)-/); // Get "items-3" from "items-3-fieldname" (example)
            let prefix;
            if (m) {
                prefix = m[1];
            } else {
                // fallback: remove the element if we can't determine the prefix
                item.remove();
                return;
            }

            // Create hidden DELETE input so that Django can ignore the form
            const hiddenDelete = document.createElement('input');
            hiddenDelete.type = 'hidden';
            hiddenDelete.name = `${prefix}-DELETE`;
            hiddenDelete.value = 'on';
            item.appendChild(hiddenDelete);

            item.style.display = "none";
        }
    });

});
