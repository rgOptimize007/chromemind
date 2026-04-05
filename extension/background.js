async function fetchTabsAndGroups() {
  const tabs = await chrome.tabs.query({});
  const groups = await chrome.tabGroups.query({});
  
  const groupMap = {};
  groups.forEach(g => {
    groupMap[g.id] = g.title || "Unnamed Group";
  });

  const result = tabs.map(t => ({
    url: t.url,
    title: t.title,
    tab_group_name: t.groupId !== -1 ? groupMap[t.groupId] : null
  })).filter(t => t.url);

  return result;
}

// Poll local Python server. If it's active, send data.
setInterval(async () => {
  try {
    const data = await fetchTabsAndGroups();
    await fetch("http://localhost:9223/submit_tabs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  } catch (e) {
    // Expected when python script is not running
  }
}, 2000);
