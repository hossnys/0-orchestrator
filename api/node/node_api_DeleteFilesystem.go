package node

import (
	"fmt"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/zero-os/0-orchestrator/api/tools"
)

// DeleteFilesystem is the handler for DELETE /nodes/{nodeid}/storagepools/{storagepoolname}/filesystem/{filesystemname}
// Delete filesystem
func (api NodeAPI) DeleteFilesystem(w http.ResponseWriter, r *http.Request) {
	aysClient := tools.GetAysConnection(r, api)
	vars := mux.Vars(r)
	name := vars["filesystemname"]

	// execute the delete action of the snapshot
	blueprint := map[string]interface{}{
		"actions": []tools.ActionBlock{{
			Action:  "delete",
			Actor:   "filesystem",
			Service: name,
			Force:   true,
		}},
	}

	run, err := aysClient.ExecuteBlueprint(api.AysRepo, "filesystem", name, "delete", blueprint)
	errmsg := "Error executing blueprint for filesystem deletion "
	if !tools.HandleExecuteBlueprintResponse(err, w, errmsg) {
		return
	}

	// Wait for the delete job to be finshed before we delete the service
	if _, err = aysClient.WaitRunDone(run.Key, api.AysRepo); err != nil {
		httpErr, ok := err.(tools.HTTPError)
		if ok {
			tools.WriteError(w, httpErr.Resp.StatusCode, httpErr, "Error running blueprint for filesystem deletion")
		} else {
			tools.WriteError(w, http.StatusInternalServerError, err, "Error running blueprint for filesystem deletion ")
		}
		return
	}

	resp, err := aysClient.Ays.DeleteServiceByName(name, "filesystem", api.AysRepo, nil, nil)
	if err != nil {
		errmsg := "Error deleting filesystem services "
		tools.WriteError(w, http.StatusInternalServerError, err, errmsg)
		return
	}

	if resp.StatusCode != http.StatusNoContent {
		errmsg := fmt.Sprintf("Error deleting filesystem services : %+v", resp.Status)
		tools.WriteError(w, resp.StatusCode, fmt.Errorf("bad response from AYS: %s", resp.Status), errmsg)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
