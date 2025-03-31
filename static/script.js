function searchBtn(){
    document.getElementById('search-btn').innerHTML = `
    <form method="post" action="getnews">
    {% csrf_token %}
    <input type="text" name="newsType">
    <button type="submit" style="border: none; background: none; padding-inline: 7px;">
      🔍
    </button>
    </form>`
  }


  function searchBtn2(){
    document.getElementById('search-btn').innerHTML = "<span onclick='searchBtn()' style='cursor: pointer;'>🔍</span>"
  }