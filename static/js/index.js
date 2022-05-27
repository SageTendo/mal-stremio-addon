function copy_to_clipboard() {
  /* Get the text field */
  var copyText = document.getElementById("manifest_url");

  /* Select the text field */
  copyText.setSelectionRange(0, copyText.value.length); /* For mobile devices */

   /* Copy the text inside the text field */
  try {
    navigator.clipboard.writeText(copyText.value);
  } catch (Exception) {
    document.execCommand('copy')
  }

  /* Alert the copied text */
  alert("Copied Manifest URL to clipboard");
}