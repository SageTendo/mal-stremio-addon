function copy_to_clipboard() {
    /* Get the text field */
    let copyText = document.getElementById("manifest_url");

    /* Select the text field */
    copyText.setSelectionRange(0, copyText.value.length); /* For mobile devices */

    /* Copy the text inside the text field */
    try {
        navigator.clipboard.writeText(copyText.value).then(() => alert("Copied Manifest URL to clipboard"));
    } catch (Exception) {
        try {
            // noinspection JSDeprecatedSymbols
            document.execCommand('copy')
        } catch (Exception) {
            alert("Failed to copy to clipboard");
        }
    }
}

function toast() {
    /* Get the snackbar DIV */
    let x = document.getElementById("toast");
    x.show();
}
