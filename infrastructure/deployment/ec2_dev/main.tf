data "aws_ami" "ubuntu_2204" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20220912"]
  }
}

resource "tls_private_key" "ec2_ssh_key_rsa" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "ec2_ssh_key" {
  key_name   = var.key_name
  public_key = tls_private_key.ec2_ssh_key_rsa.public_key_openssh
}

resource "local_file" "ec2_ssh_key" {
    content  = tls_private_key.ec2_ssh_key_rsa.private_key_pem
    filename = var.ssh_key_filename
}

resource "aws_instance" "ec2_instance" {
  ami = data.aws_ami.ubuntu_2204.id
  instance_type = var.instance_type

  root_block_device {
    volume_type = "gp2"
    volume_size = var.volume_size
  }

  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.id

  key_name = aws_key_pair.ec2_ssh_key.key_name

  vpc_security_group_ids = var.security_groups

  tags = var.tags

  user_data_replace_on_change = true

  user_data = var.user_data

  monitoring              = false
  disable_api_termination = false
  # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination
}

output "external_ip" {
  value = aws_instance.ec2_instance.public_ip
}
