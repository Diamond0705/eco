(function () {
    function normalizeRussianPhone(value) {
        var digits = value.replace(/\D/g, "");
        if (digits.length === 11 && (digits[0] === "7" || digits[0] === "8")) {
            digits = digits.slice(1);
        }
        if (digits.length !== 10 || digits[0] !== "9") {
            return value;
        }
        return "+7 (" + digits.slice(0, 3) + ") " + digits.slice(3, 6) + "-"
            + digits.slice(6, 8) + "-" + digits.slice(8, 10);
    }

    function parseCargoWeight(value) {
        if (!value) {
            return null;
        }
        var normalized = String(value).replace(/\s/g, "").replace(",", ".");
        var parsed = Number(normalized);
        return Number.isFinite(parsed) ? parsed : null;
    }

    function formatKg(value) {
        if (value === null || value === undefined || value === "") {
            return "";
        }
        var rounded = Math.round(Number(value) * 100) / 100;
        return String(rounded).replace(".", ",");
    }

    function initTransportCapacityHint() {
        var dataNode = document.getElementById("transport-capacity-data");
        var transportSelect = document.getElementById("id_transport");
        var weightInput = document.getElementById("id_cargo_weight_kg");
        var hint = document.querySelector("[data-order-capacity-hint]");

        if (!dataNode || !transportSelect || !weightInput || !hint) {
            return;
        }

        var capacityData = {};
        try {
            capacityData = JSON.parse(dataNode.textContent || "{}");
        } catch (error) {
            return;
        }

        function updateHint() {
            var selected = capacityData[transportSelect.value];
            var weight = parseCargoWeight(weightInput.value);

            hint.classList.remove(
                "order-capacity-hint-visible",
                "order-capacity-hint-ok",
                "order-capacity-hint-warning"
            );
            hint.textContent = "";

            if (!selected || !selected.capacity_kg) {
                return;
            }

            hint.classList.add("order-capacity-hint-visible");

            if (weight === null) {
                hint.textContent = "Грузоподъемность: " + formatKg(selected.capacity_kg) + " кг";
                return;
            }

            if (weight <= Number(selected.capacity_kg)) {
                hint.classList.add("order-capacity-hint-ok");
                hint.textContent = "Подходит для груза " + formatKg(weight) + " кг";
                return;
            }

            hint.classList.add("order-capacity-hint-warning");
            hint.textContent = "Не подходит: груз превышает грузоподъемность "
                + formatKg(selected.capacity_kg) + " кг";
        }

        transportSelect.addEventListener("change", updateHint);
        weightInput.addEventListener("input", updateHint);
        updateHint();
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll('input[name="phone"]').forEach(function (input) {
            input.addEventListener("blur", function () {
                input.value = normalizeRussianPhone(input.value);
            });
        });
        initTransportCapacityHint();
    });
}());
