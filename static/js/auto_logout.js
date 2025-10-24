(function () {
    const beaconUrl = window.LOGOUT_BEACON_URL || '/auth/logout_beacon';
    window.addEventListener("pagehide", function (event) {
        if (event.persisted === false) {
            try {
                this.navigator.sendBeacon(beaconUrl);
            } catch (e) {
                console.warn("Falha no sendBeacon de logout", e);
            }
        }
    });
})();