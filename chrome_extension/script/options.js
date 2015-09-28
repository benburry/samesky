// Saves options to chrome.storage.sync.
function save_options() {
  var endpoint_url = document.getElementById('endpoint_url').value;
  chrome.storage.sync.set({
    endpoint_url: endpoint_url
  }, function() {
    // Update status to let user know options were saved.
    var status = document.getElementById('status');
    status.textContent = 'Options saved.';
    setTimeout(function() {
      status.textContent = '';
    }, 750);
  });
}

// Restores select box and checkbox state using the preferences
// stored in chrome.storage.
function restore_options() {
  chrome.storage.sync.get({
    endpoint_url: 'http://home.burry.name:5000'
  }, function(items) {
    document.getElementById('endpoint_url').value = items.endpoint_url;
    document.getElementById('like').checked = items.likesColor;
  });
}
document.addEventListener('DOMContentLoaded', restore_options);
document.getElementById('save').addEventListener('click', save_options);
