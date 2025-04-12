if [ -z "$TEST" ]; then
    echo ""
    echo "Missing required test env" >&2
    echo "export TEST=<dir> to run specified tests" >&2
    echo ""
    exit
fi

if [ -e /root/agent ]; then
    source /root/agent > /dev/null
fi

if [ -z "$TMPDIR" ]; then
    export TMPDIR=$(mktemp -d)
    chmod go+rwx $TMPDIR
fi

load $TEST/config.bash


setup() {
 aa-teardown >/dev/null || true
}

@test "Setup / download vm image ${IMG_URL} to ${TMPDIR}/${VM_IMAGE}" {
    rm -f  ${TMPDIR}/${VM_IMAGE}
    qemu-img create -f qcow2 ${TMPDIR}/${VM_IMAGE} 20M
    # create data blocks included in full backup that is then zeroed
    # between incremental backup
    qemu-io -c "write 15M 256k" ${TMPDIR}/${VM_IMAGE}
    qemu-io -c "write 17M 256k" ${TMPDIR}/${VM_IMAGE}

    # create reference image
    REFIMAGE=${TMPDIR}/reference.qcow2
    rm -f ${REFIMAGE}
    qemu-img create -f qcow2 ${REFIMAGE} 20M

    # how image should look like after restore (no zeroed blocks included)
    # but same amount of data blocks
    qemu-io -c "write 15M 256k" ${REFIMAGE}
    qemu-io -c "write 17M 256k" ${REFIMAGE}
    qemu-io -c "write 1M 64k" ${REFIMAGE}
    qemu-io -c "write 1M 64k" ${REFIMAGE}
    qemu-io -c "write 127k 64k" ${REFIMAGE}
    qemu-io -c "write 5000k 64k" ${REFIMAGE}
}
@test "Setup: Define and start test VM ${VM}" {
    virsh destroy ${VM} || true
    echo "output = ${output}"
    virsh undefine ${VM} --remove-all-storage --checkpoints-metadata || true
    echo "output = ${output}"
    cp ${VM}/${VM}.xml ${TMPDIR}/
    sed -i "s|__TMPDIR__|${TMPDIR}|g" ${TMPDIR}/${VM}.xml
    run virsh define ${TMPDIR}/${VM}.xml
    echo "output = ${output}"
    run virsh start ${VM}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    echo "output = ${output}"
}
@test "Backup: create full backup" {
    run ../virtnbdbackup -d $VM -l full -o ${TMPDIR}/fstrim
    [[ "${output}" =~  "Saved qcow image config" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Change one 64k block with data" {
    run qemu-io -c "write 1M 64k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create incremental backup: one data block must be detected" {
    run ../virtnbdbackup -d $VM -l inc -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Got 1 extents to backup" ]]
    [[ "${output}" =~  "65536 bytes [64.0KiB] of data extents to backup" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM 1" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Change one 64k block with data two 64k block with zeroes" {
    run qemu-io -c "write 1M 64k" ${TMPDIR}/${VM_IMAGE}
    run qemu-io -c "write -z 2M 64k" ${TMPDIR}/${VM_IMAGE}
    run qemu-io -c "write -z 3M 64k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM 1" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create incremental backup: only one data block must be detected" {
    run ../virtnbdbackup -d $VM -l inc -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Got 1 extents to backup" ]]
    [[ "${output}" =~  "Detected 65536 bytes [64.0KiB] non-sparse blocks for current bitmap" ]]
    [[ "${output}" =~  "65536 bytes [64.0KiB] of data extents to backup" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM 2" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Change one 64k block with data, overlapping 64k block with zeroes" {
    run qemu-io -c "write -z 64k 64k" ${TMPDIR}/${VM_IMAGE}
    run qemu-io -c "write 127k 64k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM 2" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create incremental backup: two extents must be backed up" {
    run ../virtnbdbackup -d $VM -l inc -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Got 2 extents to backup" ]]
    [[ "${output}" =~  "Detected 131072 bytes [128.0KiB] non-sparse blocks for current bitmap" ]]
    [[ "${output}" =~  "131072 bytes [128.0KiB] of data extents to backup" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM 3" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Change one 64k block zeroes, overlapping 64k block with data" {
    run qemu-io -c "write 5000k 64k" ${TMPDIR}/${VM_IMAGE}
    run qemu-io -c "write -z 5012k 64k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM 3" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create incremental backup: three extents must be backed up" {
    run ../virtnbdbackup -d $VM -l inc -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Got 3 extents to backup" ]]
    [[ "${output}" =~  "Detected 131072 bytes [128.0KiB] non-sparse blocks for current bitmap" ]]
    [[ "${output}" =~  "131072 bytes [128.0KiB] of data extents to backup" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM 4" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Overwrite data block from before full backup with zeroes" {
    run qemu-io -c "write -z 15M 256k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM 4" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create incremental backup again" {
    run ../virtnbdbackup -d $VM -l inc -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Destroy VM 5" {
    run virsh destroy $VM
    [ "$status" -eq 0 ]
}
@test "Overwrite data block from before full backup with zeroes again" {
    run qemu-io -c "write -z 17M 256k" ${TMPDIR}/${VM_IMAGE}
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM 5" {
    run virsh start $VM
    [ "$status" -eq 0 ]
}
@test "Backup: create differencial backup with sparse detection: zero extents must be backed up" {
    run ../virtnbdbackup -d $VM -l diff -o ${TMPDIR}/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Got 0 extents to backup" ]]
    [ "$status" -eq 0 ]
}
@test "Restore" {
    run ../virtnbdrestore -i ${TMPDIR}/fstrim -o ${TMPDIR}/restore
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Compare allocation map between restored and reference image" {
    run qemu-img map --output json ${TMPDIR}/reference.qcow2 > ${TMPDIR}/map_reference.json
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run qemu-img map --output json ${TMPDIR}/restore/fstrimsmall.qcow2 > ${TMPDIR}/map_restore.json
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    cmp ${TMPDIR}/map_reference.json ${TMPDIR}/map_restore.json
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
