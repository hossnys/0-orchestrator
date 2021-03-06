package node

import (
	"gopkg.in/validator.v2"
)

type Bridge struct {
	Setting BridgeCreateSetting `json:"setting" validate:"nonzero"`
	Name    string              `json:"name" validate:"nonzero"`
	Status  EnumBridgeStatus    `json:"status" validate:"nonzero"`
}

func (s Bridge) Validate() error {

	return validator.Validate(s)
}
