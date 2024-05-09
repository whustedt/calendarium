        // This was used before there was a backend to fill static data into the timeline.
        
        function fillCalendar() {

            function getDelta(targetDate) {
                return (targetDate - todayDate) / 1000 / 60 / 60 / 24;
            }

            function formatDate(date) {
                const options = { day: 'numeric', month: 'short' };
                return date.toLocaleDateString('de-DE', options);
            }

            let data = [
                {date: new Date(2024, 3, 1), type: 'release', title: 'Entwicklungsende 1.2', description: null},
                {date: new Date(2024, 3, 15), type: 'custom', title: 'Betriebsversammlung', description: null},
                {date: new Date(2024, 4, 28), type: 'birthday', title: 'Klaus Meyer Geburtstag', description: null},
                {date: new Date(2024, 5, 4), type: 'birthday', title: 'Sandras Geburtstag', description: null},
                {date: new Date(2024, 5, 6), type: 'cake', title: 'Geburtstagskuchen', description: 'von Lisa'},
                {date: new Date(2024, 5, 11), type: 'release', title: 'iVAS-Release 9.43', description: null},
                {date: new Date(2024, 5, 12), type: 'birthday', title: 'Max\' Geburtstag', description: null},
                {date: new Date(2024, 5, 13), type: 'cake', title: '?', description: 'von Max'},
                {date: new Date(2024, 5, 13), type: 'birthday', title: 'Bronks Geburtstag', description: null},
                {date: new Date(2024, 5, 18), type: 'birthday', title: 'Momos Geburtstag', description: null}
            ];

            let todayDate = new Date().setHours(0, 0, 0, 0); // Date ohne Time
            let timelineContainer = document.querySelector(".timeline");

            for (let entry of data) {
                entryDiv = document.createElement('div');
                entryDiv.classList.add('timeline-item');
                entryDiv.classList.add(entry.type);
                entry.date.setMonth(entry.date.getMonth() - 1); // Date korrigieren wegen JS-Quatsch
                delta = getDelta(entry.date);
                if (delta < 0) {
                    entryDiv.classList.add('past');
                } else if (delta == 0) {
                    entryDiv.classList.add('highlight');
                }
                spanDate = document.createElement('span');
                spanDate.classList.add('date');
                spanDate.innerHTML = formatDate(entry.date);
                entryDiv.appendChild(spanDate);
                spanTitle = document.createElement('span');
                spanTitle.classList.add('title');
                spanTitle.innerHTML = entry.title;
                entryDiv.appendChild(spanTitle);
                if (entry.description) {
                    spanDescription = document.createElement('span');
                    spanDescription.classList.add('description');
                    spanDescription.innerHTML = entry.description;
                    entryDiv.appendChild(spanDescription);
                }
                timelineContainer.appendChild(entryDiv);
            }

            // Initial Focus setzen (Scroll-Position)
            pastEntries = document.querySelectorAll('.past');
            if (pastEntries.length >= 2) {
                pastEntries[pastEntries.length - 2].classList.add('initial-focus');
            }

        }
        fillCalendar();