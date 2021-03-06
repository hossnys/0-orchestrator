package node

import (
	"gopkg.in/validator.v2"
)

// Definition of a virtual disk
type VDiskLink struct {
	MaxIOps int    `json:"maxIOps" yaml:"maxIOps" validate:"nonzero"`
	Vdiskid string `json:"vdiskid" yaml:"vdiskid" validate:"nonzero"`
}

func (s VDiskLink) Validate() error {

	return validator.Validate(s)
}
