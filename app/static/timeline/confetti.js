        function startConfettiAnimation() {
            function toRGB(red, green, blue) {
                return "rgb(" + red + "," + green + "," + blue + ")";
            }
            function interpolate(start, end, fraction) {
                return (1 - Math.cos(Math.PI * fraction)) / 2 * (end - start) + start;
            }
            function createSplinePoints() {
                var keyPoints = [intervalStart, 1 - intervalStart], 
                    remainingInterval = 1 - totalIntervalWidth, 
                    splinePoints = [0, 1];
                while (remainingInterval) {
                    var index,
                        length,
                        currentInterval,
                        randomPoint,
                        totalWidth,
                        startPoint,
                        endPoint,
                        leftLimit,
                        rightLimit,
                        newRandomPoint = remainingInterval * Math.random();
                    for (index = 0, length = keyPoints.length, remainingInterval = 0; index < length; index += 2) {
                        if (startPoint = keyPoints[index], newRandomPoint < remainingInterval + (currentInterval = (endPoint = keyPoints[index + 1]) - startPoint)) {
                            splinePoints.push(newRandomPoint += startPoint - remainingInterval);
                            break;
                        }
                        remainingInterval += currentInterval;
                    }
                    for (leftLimit = newRandomPoint - intervalStart, rightLimit = newRandomPoint + intervalStart, index = keyPoints.length - 1; index > 0; index -= 2)
                        startPoint = keyPoints[length = index - 1],
                        endPoint = keyPoints[index],
                        startPoint >= leftLimit && startPoint < rightLimit ? endPoint > rightLimit ? keyPoints[length] = rightLimit : keyPoints.splice(length, 2) : startPoint < leftLimit && endPoint > leftLimit && (endPoint <= rightLimit ? keyPoints[index] = leftLimit : keyPoints.splice(index, 0, leftLimit, rightLimit));
                    for (index = 0, length = keyPoints.length, remainingInterval = 0; index < length; index += 2)
                        remainingInterval += keyPoints[index + 1] - keyPoints[index];
                }
                return splinePoints.sort();
            }
            function createAnimationElement(colorGenerator) {
                this.frameCount = 0,
                this.container = document.createElement("div"),
                this.content = document.createElement("div"),
                this.container.appendChild(this.content);
                var containerStyle = this.container.style,
                    contentStyle = this.content.style;
                containerStyle.position = "absolute",
                containerStyle.width = baseSize + sizeVariation * Math.random() + "px",
                containerStyle.height = baseSize + sizeVariation * Math.random() + "px",
                contentStyle.width = "100%",
                contentStyle.height = "100%",
                contentStyle.backgroundColor = colorGenerator(),
                containerStyle.perspective = "50px",
                containerStyle.transform = "rotate(" + 360 * Math.random() + "deg)",
                this.rotationAxis = "rotate3D(" + Math.cos(360 * Math.random()) + "," + Math.cos(360 * Math.random()) + ",0,",
                this.angle = 360 * Math.random(),
                this.angleChangePerFrame = angleStart + angleVariation * Math.random(),
                contentStyle.transform = this.rotationAxis + this.angle + "deg)",
                this.xPosition = window.innerWidth * Math.random(),
                this.yPosition = -gravity,
                this.horizontalSpeed = Math.sin(minHorizontalSpeed + horizontalSpeedVariation * Math.random()),
                this.verticalSpeed = baseVerticalSpeed + verticalSpeedVariation * Math.random(),
                containerStyle.left = this.xPosition + "px",
                containerStyle.top = this.yPosition + "px",
                this.splineXCoordinates = createSplinePoints(),
                this.splineYCoordinates = [];
                for (var i = 1, length = this.splineXCoordinates.length - 1; i < length; ++i)
                    this.splineYCoordinates[i] = gravity * Math.random();
                this.splineYCoordinates[0] = this.splineYCoordinates[length] = gravity * Math.random(),
                this.update = function(limit, timeDelta) {
                    this.frameCount += timeDelta,
                    this.xPosition += this.horizontalSpeed * timeDelta,
                    this.yPosition += this.verticalSpeed * timeDelta,
                    this.angle += this.angleChangePerFrame * timeDelta;
                    for (var fraction = this.frameCount % 7777 / 7777, i = 0, nextIndex = 1; fraction >= this.splineXCoordinates[nextIndex];)
                        i = nextIndex++;
                    var yPositionChange = interpolate(this.splineYCoordinates[i], this.splineYCoordinates[nextIndex], (fraction - this.splineXCoordinates[i]) / (this.splineXCoordinates[nextIndex] - this.splineXCoordinates[i]));
                    return fraction *= 2 * Math.PI, containerStyle.left = this.xPosition + yPositionChange * Math.cos(fraction) + "px", containerStyle.top = this.yPosition + yPositionChange * Math.sin(fraction) + "px", contentStyle.transform = this.rotationAxis + this.angle + "deg)", this.yPosition > limit + gravity;
                };
            }
            function initializeAnimation() {
                if (!animationFrameRequest) {
                    document.body.appendChild(containerElement);
                    var initialColorFunction = colorFunctions[0];
                    (function addElement() {
                        var animationElement = new createAnimationElement(initialColorFunction);
                        elements.push(animationElement),
                        containerElement.appendChild(animationElement.container),
                        timeoutHandle = setTimeout(addElement, elementSpawnInterval * Math.random());
                    })();
                    var lastTimestamp = undefined;
                    requestAnimationFrame((function frameCallback(currentTimestamp) {
                        var timeDelta = lastTimestamp ? currentTimestamp - lastTimestamp : 0;
                        lastTimestamp = currentTimestamp;
                        for (var screenLimit = window.innerHeight, index = elements.length - 1; index >= 0; --index)
                            elements[index].update(screenLimit, timeDelta) && (containerElement.removeChild(elements[index].container), elements.splice(index, 1));
                        if (timeoutHandle || elements.length)
                            return animationFrameRequest = requestAnimationFrame(frameCallback);
                        document.body.removeChild(containerElement),
                        animationFrameRequest = undefined;
                    }));
                }
            }
            var MathRandom = Math.random,
                MathCos = Math.cos,
                MathSin = Math.sin,
                PI = Math.PI,
                twoPI = 2 * PI,
                timeoutHandle = undefined,
                animationFrameRequest = undefined,
                elements = [],
                elementSpawnInterval = 40,
                baseSize = 3,
                sizeVariation = 9,
                gravity = 100,
                minHorizontalSpeed = -.1,
                horizontalSpeedVariation = 0.2,
                baseVerticalSpeed = .13,
                verticalSpeedVariation = .05,
                angleStart = .4,
                angleVariation = .3,
                colorFunctions = [
                    function() { return toRGB(200 * MathRandom() | 0, 200 * MathRandom() | 0, 200 * MathRandom() | 0); },
                    function() { var colorVal = 200 * MathRandom() | 0; return toRGB(200, colorVal, colorVal); },
                    function() { var colorVal = 200 * MathRandom() | 0; return toRGB(colorVal, 200, colorVal); },
                    function() { var colorVal = 200 * MathRandom() | 0; return toRGB(colorVal, colorVal, 200); },
                    function() { return toRGB(200, 100, 200 * MathRandom() | 0); },
                    function() { return toRGB(200 * MathRandom() | 0, 200, 200); },
                    function() { var colorVal = 256 * MathRandom() | 0; return toRGB(colorVal, colorVal, colorVal); },
                    function() { return colorFunctions[MathRandom() < .5 ? 1 : 2](); },
                    function() { return colorFunctions[MathRandom() < .5 ? 3 : 5](); },
                    function() { return colorFunctions[MathRandom() < .5 ? 2 : 4](); }
                ],
                intervalStart = 1 / 10,
                totalIntervalWidth = intervalStart + intervalStart,
                containerElement = document.createElement("div");
            containerElement.style.position = "fixed",
            containerElement.style.top = "0",
            containerElement.style.left = "0",
            containerElement.style.width = "100%",
            containerElement.style.height = "0",
            containerElement.style.overflow = "visible",
            containerElement.style.zIndex = "9999",
            initializeAnimation();
        }
        if (document.querySelector(".birthday.highlight")) {
            startConfettiAnimation();
        }