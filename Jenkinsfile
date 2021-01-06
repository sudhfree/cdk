pipeline {
    agent any
    //{
      //  dockerfile {
	//	args "-v /etc/passwd:/etc/passwd"
	//	}
      //   }

    stages {
        stage('Hello') {
            steps {
                script{
                
                def image = docker.build('test:1.0')

                docker.image('test:1.0').withRun('-u 996:993 -w /var/lib/jenkins/workspace/try -v /var/lib/jenkins/workspace/try:/var/lib/jenkins/workspace/try:rw,z -v /var/lib/jenkins/workspace/try@tmp:/var/lib/jenkins/workspace/try@tmp:rw,z'){
                //image.inside
                    
        /* Run some tests which require MySQL */
                sh '''cd deployment
                      ls
                      pip install --no-cache-dir -r requirements.cdk.txt
                      cdk synth
                      cdk deploy
                      '''
                }
                }
                

                   
            }
        }
    }
}

