document.addEventListener("DOMContentLoaded", function () {
  const commentForm = document.getElementById("commentForm");
  const pageSizeSelect = document.getElementById("pageSize");
  let currentVideoUrl = "";
  let currentCommentCount = 0;
  let allComments = [];
  let currentPage = 1;

  commentForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const videoUrl = document.getElementById("videoUrl").value;
    const commentCount = parseInt(
      document.getElementById("commentCount").value
    );

    document.getElementById("loader").style.display = "block";
    document.getElementById("results").style.display = "none";

    currentVideoUrl = videoUrl;
    currentCommentCount = commentCount;
    currentPage = 1; // Reset to first page on new fetch

    try {
      await fetchAllComments(videoUrl, commentCount);
    } catch (error) {
      alert("Error: " + error.message);
      document.getElementById("loader").style.display = "none";
    }
  });

  pageSizeSelect.addEventListener("change", function () {
    if (allComments.length > 0) {
      const pageSize = parseInt(pageSizeSelect.value);
      const oldPageSize = parseInt(
        pageSizeSelect.dataset.currentSize || pageSize
      );

      // Recalculate the current page based on the new page size
      const firstCommentIndex = (currentPage - 1) * oldPageSize;
      currentPage = Math.floor(firstCommentIndex / pageSize) + 1;

      // Update the current page size in the dataset
      pageSizeSelect.dataset.currentSize = pageSize;

      // Re-render the comments for the new page
      renderPagedComments();
    }
  });

  async function fetchAllComments(videoUrl, commentCount) {
    const response = await fetch("/api/comments/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        video_url: videoUrl,
        comment_count: commentCount,
      }),
    });

    if (!response.ok) {
      let errorText = "Failed to fetch comments";
      try {
        const error = await response.json();
        errorText = error.detail || errorText;
      } catch (e) {}
      throw new Error(errorText);
    }

    const data = await response.json();
    allComments = data.comments;
    document.getElementById("videoTitle").textContent = data.video_title;

    // Store the current page size
    pageSizeSelect.dataset.currentSize = pageSizeSelect.value;

    // Render the first page of comments
    renderPagedComments();
  }

  function renderPagedComments() {
    const pageSize = parseInt(pageSizeSelect.value);
    const totalComments = allComments.length;
    const totalPages = Math.ceil(totalComments / pageSize);

    // Ensure current page is valid
    if (currentPage < 1) currentPage = 1;
    if (currentPage > totalPages) currentPage = totalPages;

    // Calculate start and end indices for current page
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, totalComments);

    // Get comments for current page
    const commentsForPage = allComments.slice(startIndex, endIndex);

    // Update pagination info
    document.getElementById("currentPage").textContent = currentPage;
    document.getElementById("totalPages").textContent = totalPages;
    document.getElementById("totalComments").textContent = totalComments;

    // Render comments for current page
    renderComments(commentsForPage);

    // Render pagination controls
    renderPagination(totalPages, currentPage);

    document.getElementById("loader").style.display = "none";
    document.getElementById("results").style.display = "block";
  }

  function renderComments(comments) {
    const commentsList = document.getElementById("commentsList");
    commentsList.innerHTML = "";

    comments.forEach((comment) => {
      const date = new Date(comment.published_at).toLocaleDateString();
      const commentCard = document.createElement("div");
      commentCard.className = "card comment-card";

      const sentimentClass = `sentiment-${comment.sentiment}`;

      commentCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title mb-0">${comment.author}</h5>
                        <span class="sentiment-tag ${sentimentClass}">${
        comment.sentiment.charAt(0).toUpperCase() + comment.sentiment.slice(1)
      }</span>
                    </div>
                    <h6 class="card-subtitle mb-2 text-muted">Published: ${date} · Likes: ${
        comment.like_count
      }</h6>
                    <p class="card-text">${comment.text}</p>
                </div>
            `;
      commentsList.appendChild(commentCard);
    });
  }

  function renderPagination(totalPages, currentPage) {
    const pagination = document.getElementById("pagination");
    pagination.innerHTML = "";

    // Previous button
    const prevLi = document.createElement("li");
    prevLi.className = `page-item ${currentPage === 1 ? "disabled" : ""}`;
    const prevLink = document.createElement("a");
    prevLink.className = "page-link";
    prevLink.href = "#";
    prevLink.textContent = "Previous";
    if (currentPage > 1) {
      prevLink.addEventListener("click", (e) => {
        e.preventDefault();
        currentPage--;
        renderPagedComments();
      });
    }
    prevLi.appendChild(prevLink);
    pagination.appendChild(prevLi);

    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(startPage + maxVisiblePages - 1, totalPages);

    if (endPage - startPage < maxVisiblePages - 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      const pageLi = document.createElement("li");
      pageLi.className = `page-item ${i === currentPage ? "active" : ""}`;
      const pageLink = document.createElement("a");
      pageLink.className = "page-link";
      pageLink.href = "#";
      pageLink.textContent = i;
      pageLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (i !== currentPage) {
          currentPage = i;
          renderPagedComments();
        }
      });
      pageLi.appendChild(pageLink);
      pagination.appendChild(pageLi);
    }

    // Next button
    const nextLi = document.createElement("li");
    nextLi.className = `page-item ${
      currentPage === totalPages ? "disabled" : ""
    }`;
    const nextLink = document.createElement("a");
    nextLink.className = "page-link";
    nextLink.href = "#";
    nextLink.textContent = "Next";
    if (currentPage < totalPages) {
      nextLink.addEventListener("click", (e) => {
        e.preventDefault();
        currentPage++;
        renderPagedComments();
      });
    }
    nextLi.appendChild(nextLink);
    pagination.appendChild(nextLi);
  }
});
