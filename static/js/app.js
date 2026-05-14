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

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll('input[name="phone"]').forEach(function (input) {
            input.addEventListener("blur", function () {
                input.value = normalizeRussianPhone(input.value);
            });
        });
    });
}());
