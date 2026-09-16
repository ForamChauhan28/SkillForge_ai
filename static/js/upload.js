document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('resume-upload');
    const uploadSpinner = document.getElementById('upload-spinner');
    const uploadSection = document.getElementById('upload-section');
    const skillsSection = document.getElementById('skills-section');
    const categorizedSkills = document.getElementById('categorized-skills');
    const dreamJobSection = document.getElementById('dream-job-section');

    // Generator logic
    const generateBtn = document.getElementById('generate-btn');
    const dreamJobInput = document.getElementById('dream-job-input');
    const generateSpinner = document.getElementById('generate-spinner');
    const loadingMsg = document.getElementById('loading-msg');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleUpload(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                handleUpload(fileInput.files[0]);
            }
        });
    }

    async function handleUpload(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file.');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            alert('File size must be less than 5MB.');
            return;
        }

        if (dropZone) dropZone.classList.add('hidden');
        if (uploadSpinner) uploadSpinner.classList.remove('hidden');

        const formData = new FormData();
        formData.append('resume', file);

        try {
            const response = await fetch('/api/upload-resume', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.success) {
                // Reload the page to show updated data from server
                // This is the safest approach since the server sets skills, ATS score etc.
                window.location.reload();
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Upload failed. Please try again.');
            if (dropZone) dropZone.classList.remove('hidden');
            if (uploadSpinner) uploadSpinner.classList.add('hidden');
        }
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const job = dreamJobInput ? dreamJobInput.value.trim() : '';
            if (!job) {
                alert('Please enter your dream job.');
                return;
            }

            generateBtn.classList.add('hidden');
            if (generateSpinner) generateSpinner.classList.remove('hidden');

            const msgs = [
                'Analyzing your skill gaps...',
                'Mapping required competencies...',
                'Building personalized learning path...',
                'Generating project recommendations...',
                'Preparing interview questions...',
                'Finalizing your roadmap...'
            ];
            let msgIdx = 0;
            const msgInterval = setInterval(() => {
                msgIdx = (msgIdx + 1) % msgs.length;
                if (loadingMsg) loadingMsg.textContent = msgs[msgIdx];
            }, 3000);

            try {
                // Generate roadmap — send dream_job in the request body
                const response = await fetch('/api/generate-roadmap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dream_job: job })
                });
                const result = await response.json();

                if (result.success) {
                    window.location.href = '/roadmap';
                } else {
                    const errMsg = result.error || 'Failed to generate roadmap';
                    // Check for specific API issues
                    if (errMsg.includes('429') || errMsg.includes('quota') || errMsg.includes('RESOURCE_EXHAUSTED')) {
                        throw new Error('Daily API quota reached. The free Gemini API allows limited requests per day. Please wait a few minutes and try again.');
                    }
                    if (errMsg.includes('503') || errMsg.includes('overload') || errMsg.includes('high demand')) {
                        throw new Error('The AI service is currently experiencing high demand. Please wait 1-2 minutes and try again.');
                    }
                    throw new Error(errMsg);
                }
            } catch (error) {
                console.error('Roadmap generation error:', error);
                hideLoading();
                if (typeof showToast === 'function') {
                    showToast(error.message || 'An error occurred. Please try again.', 'danger', 6000);
                } else {
                    alert(error.message || 'An error occurred while generating the roadmap. Please try again.');
                }
                generateBtn.classList.remove('hidden');
                if (generateSpinner) generateSpinner.classList.add('hidden');
            } finally {
                clearInterval(msgInterval);
            }
        });
    }
});
