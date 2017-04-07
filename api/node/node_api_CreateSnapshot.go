package node

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/g8os/grid/api/tools"
	"github.com/gorilla/mux"

	log "github.com/Sirupsen/logrus"
)

// CreateSnapshot is the handler for POST /nodes/{nodeid}/storagepools/{storagepoolname}/filesystem/{filesystemname}/snapshot
// Create a new readonly filesystem of the current state of the volume
func (api NodeAPI) CreateSnapshot(w http.ResponseWriter, r *http.Request) {
	filessytem := mux.Vars(r)["filesystemname"]

	var name string

	// decode request
	if err := json.NewDecoder(r.Body).Decode(&name); err != nil {
		tools.WriteError(w, http.StatusBadRequest, err)
		return
	}

	bpContent := struct {
		Filesystem string `json:"filesystem"`
		Name       string `json:"name"`
	}{

		Filesystem: filessytem,
		Name:       name,
	}

	blueprint := map[string]interface{}{
		fmt.Sprintf("fssnapshot__%s", name): bpContent,
		"actions":                           []map[string]string{{"action": "install"}},
	}

	if _, err := tools.ExecuteBlueprint(api.AysRepo, "fssnapshot", name, "install", blueprint); err != nil {
		httpErr := err.(tools.HTTPError)
		log.Errorf("Error executing blueprint for fssnapshot creation : %+v", err.Error())
		tools.WriteError(w, httpErr.Resp.StatusCode, httpErr)
	}
}
